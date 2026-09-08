"""Opt-in scoped operator commands; never exposed through the browser API."""
import json
from http.client import HTTPException
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.error import HTTPError
from urllib.parse import quote

from .provider import ItsAPlan,NoRedirect,MAX_BYTES
from .model import validate_snapshot,utcnow
from .reporting import digest,locked


class OperatorProvider(ItsAPlan):
    def request(self,method,path,body=None):
        token=Path(self.config['token_file']).read_text().strip()
        req=Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,
                    headers={'x-api-key':token,'Content-Type':'application/json','Accept':'application/json'},method=method)
        try:
            with build_opener(NoRedirect()).open(req,timeout=10) as response:raw=response.read(MAX_BYTES+1)
        except HTTPError as exc:raise OSError('Provider request rejected: HTTP '+str(exc.code)) from None
        except HTTPException:raise OSError('Provider transport incomplete') from None
        if len(raw)>MAX_BYTES:raise ValueError('Provider response exceeds bound')
        return json.loads(raw) if raw else {}

    def inventory(self):
        key=quote(self.config['project'],safe='');project=self.get('/projects/'+key)
        field=next(f['id'] for f in project['customFields'] if f['name']==self.config.get('field','Project Intent v0'))
        rows=[]
        for issue in self.get('/projects/'+key+'/issues/board')['issues']:
            values=[v['value'] for v in issue['fieldValues'] if v['fieldId']==field and v['value']]
            record=json.loads(values[0]) if values else None
            rows.append({'native_id':issue['id'],'identifier':issue['identifier'],'title':issue['title'],
                         'record':record,'metadata_digest':digest(record),'field_id':field,'description':issue.get('description','')})
            for role in ('delegate','assignee'):
                user_id=issue.get(role+'UserId')
                member=next((m for m in project.get('assignees',[]) if m['userId']==user_id),None)
                rows[-1][role]={'user_id':user_id,'name':member.get('name') if member else None,
                               'username':member.get('username') if member else None}
            column=next((c for c in project.get('columns',[]) if c['id']==issue.get('columnId')),None)
            rows[-1]['lifecycle']=column['name'] if column else None
        return rows

    def resolve(self,reference):
        matches=[i for i in self.inventory() if reference in (i['identifier'],(i['record'] or {}).get('id'))]
        if len(matches)!=1:raise ValueError('Native assignment absent or ambiguous in configured provider project')
        return matches[0]

    def find_comment(self,issue,marker):
        cursor=None
        for _ in range(100):
            path='/issues/'+str(issue)+'/feed?limit=100'
            if cursor:path+='&cursor='+quote(json.dumps(cursor),safe='')
            result=self.get(path)
            if not isinstance(result,dict) or 'items' not in result or 'nextCursor' not in result:raise ValueError('Unsupported activity pagination')
            found=next((c for c in result['items'] if c.get('kind')=='comment' and c.get('body','').startswith(marker+'\n')),None)
            if found:return found
            cursor=result['nextCursor']
            if cursor is None:return None
        raise ValueError('Activity read incomplete; publication refused')

    def comment(self,issue,body):return self.request('POST','/issues/'+str(issue)+'/comments',{'body':body})


def configured(config,scope):
    """An explicit operator allowlist is required in addition to reader scopes."""
    if scope not in config.get('operator',{}).get('allowed_scopes',[]):raise ValueError('Scope not authorized for operator commands')
    entry=next((s for s in config['scopes'] if s['id']==scope),None)
    if not entry or entry['provider']['kind']!='itsaplan':raise ValueError('No writable provider capability for scope')
    return entry,OperatorProvider(entry['provider'])


def reconcile(provider,scope,packet,journal,expected_inventory_digest=None):
    """Compare expected metadata, preserve evidence, journal uncertainty before writes.

    Provider has no atomic compare-and-swap: operators must serialize external edits.
    This local lock prevents concurrent use of this configured publisher only.
    """
    from .runtime import read_json,write_json
    if packet.get('confirmed') is not True:raise ValueError('Confirmed existing user assignment required')
    if packet.get('scope')!=scope:raise ValueError('Packet scope differs from operator scope')
    record=packet['record']
    validate_snapshot({'version':1,'mission':'validation','source':{'authoritative':False,'captured_at':utcnow().isoformat()},'records':[record]})
    operation=digest(packet);journal=Path(journal);file=journal/(operation+'.json')
    with locked(journal):
        prior=read_json(file) if file.exists() else {}
        rows=provider.inventory();ref=packet.get('native_identifier')
        if expected_inventory_digest is not None and digest(sorted(rows,key=lambda r:r['identifier']))!=expected_inventory_digest:
            raise ValueError('Native inventory changed at mutation boundary; preview and inspect again')
        matches=[i for i in rows if i['identifier']==ref] if ref else [i for i in rows if (i['record'] or {}).get('id')==record['id'] or i['title']==packet.get('title')]
        if len(matches)>1:raise ValueError('Ambiguous native records; resolve before enrollment')
        if matches:
            issue=matches[0];old=issue['record']
            if any(i['native_id']!=issue['native_id'] and (i['record'] or {}).get('id')==record['id'] for i in rows):
                raise ValueError('Alias already belongs to another native issue')
            if old==record:
                result={'state':'published','identifier':issue['identifier'],'metadata_digest':digest(record),'operation':operation}
                write_json(file,result)
                return result
            if ref and issue['metadata_digest']!=packet.get('expected_digest'):raise ValueError('Metadata changed since inspection; reconcile the latest revision')
            if not ref and old is not None:raise ValueError('Existing candidate found; inspect and target its native identifier')
            if not ref and old is None and not str(issue.get('description','')).startswith('project-intent-enrollment:'+operation+'\n'):
                raise ValueError('Existing unannotated candidate found; inspect and target its native identifier')
            if old:
                if old['id']!=record['id']:raise ValueError('Stable alias cannot be replaced')
                if old['kind']!=record['kind']:raise ValueError('Record kind cannot be replaced')
                if record['revision']==old['revision']:raise ValueError('Changed metadata requires a new revision')
                for key in ('completion_evidence','conformance_assertions'):
                    if any(v not in record.get(key,[]) for v in old.get(key,[])):raise ValueError('Historical evidence/assertions must be retained')
        elif ref:raise ValueError('Requested native issue absent from configured project')
        else:
            if packet.get('expected_digest')!=digest(None) or not packet.get('title'):raise ValueError('Create requires title and expected digest of null')
            if prior.get('state')=='uncertain':return prior
            marker='project-intent-enrollment:'+operation
            write_json(file,{'state':'uncertain','operation':operation,'reason':'Native creation may have occurred; inspect provider before retry'})
            try:
                key=quote(provider.config['project'],safe='');p=provider.get('/projects/'+key)
                column=next(c['id'] for c in p['columns'] if c['stateType']=='unstarted')
                created=provider.request('POST','/projects/'+key+'/issues',{'columnId':column,'title':packet['title'],'description':marker+'\nConfirmed assignment; enrollment conveys no execution authority.'})
                issue=next(i for i in provider.inventory() if i['native_id']==created['id'])
            except (OSError,ValueError,KeyError,StopIteration):return read_json(file)
        write_json(file,{'state':'uncertain','operation':operation,'identifier':issue['identifier'],'reason':'Metadata write may have occurred; re-read before retry'})
        try:
            # Durable history before replacement, with full previous revision.
            marker='project-intent-reconcile:'+operation
            if not provider.find_comment(issue['native_id'],marker):
                provider.comment(issue['native_id'],marker+'\nPrevious metadata:\n'+json.dumps(issue['record'],sort_keys=True)+'\nReplacement:\n'+json.dumps(record,sort_keys=True))
            provider.request('PUT',f"/issues/{issue['native_id']}/fields/{issue['field_id']}",{'value':json.dumps(record)})
            actual=provider.resolve(issue['identifier'])
            if actual['record']!=record:raise ValueError('Provider verification differs')
        except (OSError,ValueError,KeyError):return read_json(file)
        result={'state':'published','operation':operation,'identifier':issue['identifier'],'metadata_digest':digest(record)}
        write_json(file,result);return result
