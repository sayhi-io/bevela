"""Pure, scoped Mission Control projection. No IO or provider implementation."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import PurePosixPath
import re

CONTRACT = 'sayhi.project-intent.observatory/v1'


def utcnow():
    return datetime.now(timezone.utc)


def date(value):
    if not isinstance(value,str):raise ValueError('Timestamp must be text')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return parsed


def validate_snapshot(snapshot):
    if not isinstance(snapshot,dict) or not isinstance(snapshot.get('source'),dict):
        raise ValueError('Invalid snapshot/source object')
    if snapshot.get('version') != 1 or snapshot['source'].get('authoritative') is not False:
        raise ValueError('Snapshot version/authority invalid')
    date(snapshot['source']['captured_at'])
    if not isinstance(snapshot.get('mission'), str) or not isinstance(snapshot.get('records'), list):
        raise ValueError('Invalid snapshot envelope')
    ids = set()
    for r in snapshot['records']:
        if not isinstance(r,dict) or not isinstance(r.get('id'),str):raise ValueError('Invalid record object')
        if not re.fullmatch(r'[A-Z0-9-]+', r['id']) or r['id'] in ids:
            raise ValueError('Invalid/duplicate record ID')
        ids.add(r['id'])
        if r['kind'] not in ('workstream', 'invariant', 'precedent'):
            raise ValueError('Unsupported record kind')
        for key in ('statement', 'revision', 'state'):
            if not isinstance(r.get(key), str) or not r[key]:
                raise ValueError('Invalid record '+key)
        if not isinstance(r.get('boundaries'), list) or any(not isinstance(x,str) or not x for x in r['boundaries']):
            raise ValueError('Invalid boundary keys')
        if r['kind']=='workstream':
            if not isinstance(r.get('scope'),str) or not strings(r.get('acceptance')):
                raise ValueError('Missing work scope/acceptance')
            if not isinstance(r.get('readiness',{}),dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in r.get('readiness',{}).items()):
                raise ValueError('Invalid readiness')
            if not isinstance(r.get('conformance_assertions',[]),list):raise ValueError('Invalid assertions')
            for c in r.get('conformance_assertions',[]):
                if not isinstance(c,dict) or any(not isinstance(c.get(k),str) or not c[k] for k in ('invariant','revision','subject')):
                    raise ValueError('Invalid evidence binding')
            if not strings(r.get('completion_evidence',[])):raise ValueError('Invalid evidence references')
            if not isinstance(r.get('divergences',[]),list) or any(not isinstance(d,dict) or not isinstance(d.get('status'),str) or not isinstance(d.get('reason',''),str) for d in r.get('divergences',[])):
                raise ValueError('Invalid divergence declarations')
            if r.get('handoff_at'):date(r['handoff_at'])
            if not isinstance(r.get('initiative_refs',[]),list) or any(not isinstance(i,dict) or not isinstance(i.get('scope'),str) or not isinstance(i.get('id'),(str,int)) for i in r.get('initiative_refs',[])):
                raise ValueError('Invalid initiative references')
        if not isinstance(r.get('applies_to',[]),list) or any(not isinstance(a,dict) or not isinstance(a.get('scope'),str) or not strings(a.get('boundaries')) for a in r.get('applies_to',[])):
            raise ValueError('Invalid explicit architecture applicability')
    if not isinstance(snapshot.get('initiatives',[]),list) or any(not isinstance(i,dict) or not isinstance(i.get('title'),str) or not isinstance(i.get('status'),str) or not isinstance(i.get('id'),(str,int)) for i in snapshot.get('initiatives',[])):
        raise ValueError('Invalid initiatives')
    return snapshot


def strings(value):
    return isinstance(value,list) and all(isinstance(v,str) for v in value)


def valid_presence(p, now=None):
    try:
        if not isinstance(p,dict) or p.get('status') not in ('active','inactive'):return False
        if any(not isinstance(p.get(k),str) or not p[k] for k in ('session','workstream')):return False
        if not strings(p.get('approaching',[])) or not strings(p.get('avoid',[])):return False
        for key in ('touching_paths','avoid_paths','touching_seams'):
            if not strings(p.get(key,[])):return False
        for value in p.get('touching_paths',[])+p.get('avoid_paths',[]):
            if not value or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts or any(c in value for c in '\\*?[]'):return False
        if p.get('access','unspecified') not in ('inspect','edit','unspecified'):return False
        checkout=p.get('checkout')
        if checkout is not None:
            if not isinstance(checkout,dict):return False
            if any(not isinstance(checkout.get(k),str) or not checkout[k] for k in ('root','host','repository_common_dir','observed_at')):return False
            if not PurePosixPath(checkout['root']).is_absolute() or not PurePosixPath(checkout['repository_common_dir']).is_absolute():return False
            if any(checkout.get(k) is not None and not isinstance(checkout[k],str) for k in ('head','branch')):return False
            date(checkout['observed_at'])
        expires,heartbeat=date(p['expires_at']),date(p['heartbeat_at'])
        return heartbeat <= (now or utcnow()) and 0 < (expires-heartbeat).total_seconds() <= 14400
    except (KeyError,ValueError,TypeError,AttributeError):return False


def applies(architecture, work):
    # No implicit boundary matching across products. Explicit grants are required.
    if architecture['scope_id'] == work['scope_id']:
        return bool(set(architecture['boundaries']) & set(work['boundaries']))
    return any(x.get('scope') == work['scope_id'] and
               set(x.get('boundaries', [])) & set(work['boundaries'])
               for x in architecture.get('applies_to', []))


def reconcile(work, invariants):
    subject = work.get('completion_subject')
    claims = {c['invariant']: c for c in work.get('conformance_assertions', []) if c['subject']==subject}
    result = []
    for invariant in invariants:
        claim = claims.get(invariant['id'])
        # Cross-scope bindings must use qualified invariant IDs.
        if invariant['scope_id'] != work['scope_id']:
            claim = claims.get(invariant['key'])
        status = 'no-bound-evidence'
        if claim:
            status = 'revision-current' if claim['revision']==invariant['revision'] else 'reconciliation-required'
        result.append({'invariant':invariant['key'],'statement':invariant['statement'],
            'architecture_revision':invariant['revision'],'evidence_revision':claim['revision'] if claim else None,
            'subject':subject,'status':status,'verification':'declaration comparison only'})
    return result


def project(states, allowed_scopes, selected=None, now=None):
    """Filter scope authority FIRST; all counts, links and attention derive afterward."""
    now = now or utcnow()
    allowed = set(allowed_scopes)
    if selected and selected not in allowed:
        raise PermissionError('Scope not authorized')
    authorized = [s for s in states if s['id'] in allowed]
    visible = [s for s in authorized if not selected or s['id']==selected]
    records, scopes, sessions, attention, initiatives = [], [], [], [], []
    for s in visible:
        snapshot = s.get('snapshot')
        provenance = {k:snapshot['source'][k] for k in ('provider','project','captured_at','authoritative','mode') if k in snapshot['source']} if snapshot else None
        scopes.append({'id':s['id'],'label':s['label'],'mission':snapshot['mission'] if snapshot else '',
            'provider_status':s['provider_status'],'source':provenance,
            'age_seconds':max(0,int((now-date(provenance['captured_at'])).total_seconds())) if provenance else None,
            'execution':s.get('execution', {'status':'not-connected','meaning':'No execution source enrolled'})})
        if s['provider_status'] in ('unavailable','not-yet-observed'):
            attention.append({'scope':s['id'],'kind':'provider-unavailable','message':'Provider unavailable; showing last-known snapshot' if snapshot else 'Provider unavailable; no cached state'})
        if s.get('execution',{}).get('status') in ('unavailable','partial'):
            attention.append({'scope':s['id'],'kind':'execution-unavailable','message':'Execution observations unavailable; durable intent remains visible'})
        if snapshot:
            for r in snapshot['records']:
                records.append(dict(r,scope_id=s['id'],key=s['id']+':'+r['id']))
            for i in snapshot.get('initiatives',[]):
                initiatives.append({'scope':s['id'],'id':i['id'],'title':i['title'],'status':i['status']})
        for p in s.get('presence',[]):
            try:
                if not valid_presence(p,now):continue
                if p.get('scope',s['id']) != s['id']:
                    continue
                expires, heartbeat = date(p['expires_at']), date(p['heartbeat_at'])
                if heartbeat > now or expires <= heartbeat or (expires-heartbeat).total_seconds()>14400:
                    continue
                status = 'inactive' if p['status']=='inactive' else ('active' if expires>now else 'expired')
                sessions.append({'scope':s['id'],'session':p['session'],'workstream':s['id']+':'+p['workstream'],
                    'status':status,'working':p.get('working',p.get('working_on','')),
                    'approaching':p.get('approaching',[]),'avoid':p.get('avoid',[]),
                    'heartbeat_at':p['heartbeat_at'],'expires_at':p['expires_at'],
                    'checkout':{k:p['checkout'].get(k) for k in ('host','root','repository_common_dir','branch','head','observed_at')} if isinstance(p.get('checkout'),dict) else None,
                    'access':p.get('access','unspecified'),
                    'touching_paths':p.get('touching_paths',[]),'touching_seams':p.get('touching_seams',[]),'avoid_paths':p.get('avoid_paths',[])})
            except (KeyError,ValueError,TypeError):
                continue
    architecture = [r for r in records if r['kind'] != 'workstream']
    if selected:
        # An operator authorized for the source scope may receive explicitly
        # applicable cross-scope architecture even while focusing a product.
        for source in authorized:
            if source['id']==selected or not source.get('snapshot'):continue
            for r in source['snapshot']['records']:
                a=dict(r,scope_id=source['id'],key=source['id']+':'+r['id'])
                if r['kind']!='workstream' and any(applies(a,w) for w in records if w['kind']=='workstream'):
                    architecture.append(a)
    workstreams = []
    for r in sorted((r for r in records if r['kind']=='workstream'),key=lambda x:x['key']):
        related = [a for a in architecture if a['state']=='accepted' and applies(a,r)]
        claims = reconcile(r,[a for a in related if a['kind']=='invariant'])
        workers = [p for p in sessions if p['workstream']==r['key']]
        # Explicit allowlist: do not ship provider payloads, credentials or hidden fields.
        fields = ('id','key','scope_id','title','statement','state','scope','avoid','acceptance','boundaries',
                  'readiness','completion_subject','completion_evidence','handoff_summary','handoff_at',
                  'handoff_verification','conformance_assertions','source_checkout','branch','integration_dependency',
                  'provider_id','provider_url','initiative_id','delegate_name','delegate_username','assignee_name','assignee_username','provider_identifier','provider_lifecycle')
        work = {k:r[k] for k in fields if k in r}
        source_state=next(s for s in states if s['id']==r['scope_id'])
        work['local_reports']=[report for report in source_state.get('local_reports',[]) if report.get('payload',{}).get('scope')==r['scope_id'] and report.get('payload',{}).get('workstream')==r['id']]
        work['report_coverage']=source_state.get('report_coverage','not-configured')
        work['activity']=source_state.get('activity',{}).get(r['id'],{'status':'not-connected','points':[]})
        work.update(workers=workers, claims=claims,
            precedents=[{'key':a['key'],'statement':a['statement'],'revision':a['revision']} for a in related if a['kind']=='precedent'],
            environment={'requirement':r.get('required_environment',r.get('environment')),
                         'availability':'unknown','occupancy':'unknown','meaning':'Requirement only; no substrate observation'},
            divergences=r.get('divergences',[]),
            divergence_coverage='Only explicitly recorded proposals/review findings; no automatic drift analysis')
        workstreams.append(work)
        ready = r.get('readiness',{})
        reasons = []
        if r['state']=='blocked': reasons.append(('blocked','Workstream declared blocked'))
        if ready.get('review') in ('pending','requested','awaiting-independent-review'): reasons.append(('review','Independent review pending'))
        if any(c['status']=='reconciliation-required' for c in claims): reasons.append(('architecture','Evidence binds an older/different invariant revision; reconcile, do not erase'))
        if ready.get('implementation')=='complete' and any(c['status']=='no-bound-evidence' for c in claims): reasons.append(('evidence','Completed implementation has missing invariant bindings'))
        if ready.get('merge') in ('ready','awaiting-source-seal-and-CI','needs-reconciliation'): reasons.append(('integration','Merge: '+ready['merge']))
        for d in work['divergences']:
            if d.get('status') in ('proposed','unexplained'): reasons.append(('divergence',d.get('reason','Architectural decision/review needed')))
        if r['state']=='active' and any(p['status']=='expired' for p in workers) and not any(p['status']=='active' for p in workers): reasons.append(('presence','Last registered session expired; activity now unknown'))
        for kind,message in reasons: attention.append({'scope':r['scope_id'],'workstream':r['key'],'kind':kind,'message':message})
    by_seam = defaultdict(list)
    for w in workstreams:
        if w['state'] in ('active','blocked','ready'):
            for seam in set(w['boundaries']): by_seam[(w['scope_id'],seam)].append(w['key'])
    convergence = [{'scope':scope,'boundary':seam,'workstreams':sorted(keys),
                    'meaning':'Declared semantic overlap; not a conflict, ownership, or integration approval',
                    'approaching_sessions':[p['session'] for p in sessions if p['scope']==scope and p['status']=='active' and seam in p['approaching']]}
                   for (scope,seam),keys in sorted(by_seam.items()) if len(keys)>1]
    arch = [{'key':a['key'],'scope':a['scope_id'],'kind':a['kind'],'statement':a['statement'],
             'revision':a['revision'],'state':a['state'],'boundaries':a['boundaries'],
             'workstreams':[w['key'] for w in workstreams if applies(a,w)]} for a in architecture]
    # Native initiative plus explicit qualified provider-stored cross-product refs.
    # Only authorized scope records contribute; never expose provider total counts.
    initiatives=[]
    for source in authorized:
        for i in (source.get('snapshot') or {}).get('initiatives',[]):
            members=[]
            for r in records:
                if r['kind']!='workstream':continue
                local=r['scope_id']==source['id'] and r.get('initiative_id')==i['id']
                linked=any(ref['scope']==source['id'] and ref['id']==i['id'] for ref in r.get('initiative_refs',[]))
                if local or linked:members.append(r['key'])
            if not selected or source['id']==selected or members:
                initiatives.append({'scope':source['id'],'id':i['id'],'title':i['title'],'status':i['status'],'workstreams':members})
    dependencies=[]
    imported={a['scope'] for a in arch} | {i['scope'] for i in initiatives}
    for s in authorized:
        if not selected or s['id']==selected or s['id'] not in imported:continue
        snapshot=s.get('snapshot');provenance={k:snapshot['source'][k] for k in ('provider','project','captured_at','authoritative','mode') if k in snapshot['source']} if snapshot else None
        dependencies.append({'id':s['id'],'label':s['label']+' · explicit dependency','provider_status':s['provider_status'],
            'source':provenance,'age_seconds':max(0,int((now-date(provenance['captured_at'])).total_seconds())) if provenance else None,
            'execution':{'status':'not-selected','meaning':'Only explicitly related architecture/grouping is included'}})
        if s['provider_status'] in ('unavailable','not-yet-observed'):
            attention.append({'scope':s['id'],'kind':'dependency-unavailable','message':'Related architecture/grouping uses last-known state from an unavailable source'})
    visible_keys={w['key'] for w in workstreams}
    rested=sorted((dict(p, reported_inactive_at=p['heartbeat_at']) for p in sessions
                   if p['workstream'] in visible_keys and p['status']=='inactive'
                   and 0 <= (now-date(p['heartbeat_at'])).total_seconds() <= 86400),
                  key=lambda p:(-date(p['heartbeat_at']).timestamp(),p['workstream'],p['session']))
    return {'contract':CONTRACT,'observed_at':now.isoformat(),'scopes':scopes,'workstreams':workstreams,
        'recently_rested':rested[:12],
        'rested_coverage':{'window_seconds':86400,'total':len(rested),'limit':12,
                          'meaning':'Latest explicit inactive registration per session; heartbeat is report time, not proof of completion or exact stopping time. Expired leases are excluded.'},
        'dependency_sources':dependencies,
        'architecture':arch,'sessions':sessions,'convergence':convergence,'attention':attention,'initiatives':initiatives,
        'recent_handoffs':sorted([w for w in workstreams if w.get('handoff_at')],key=lambda w:date(w['handoff_at']),reverse=True)[:12],
        'coverage':'Enrolled scopes and declared evidence only. Unknown is not healthy, safe, or authorized.',
        'read_only':True}
