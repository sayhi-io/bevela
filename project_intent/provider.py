"""Provisional read-only provider adapter; not the Project Intent product model."""
import json
from http.client import HTTPException
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse, quote
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .model import utcnow, validate_snapshot

MAX_BYTES = 8 * 1024 * 1024


class Provider(Protocol):
    def snapshot(self) -> dict: ...


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ItsAPlan:
    capabilities = ('read-workstreams','read-architecture','read-initiatives')

    def __init__(self, config):
        self.config = config
        self.base = config['url'].rstrip('/')
        u = urlparse(self.base)
        if u.username or u.password or u.query or u.fragment or (u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('localhost','127.0.0.1','::1'))):
            raise ValueError('Provider requires HTTPS or loopback HTTP without URL credentials')

    def get(self, path):
        token = Path(self.config['token_file']).read_text().strip()
        request = Request(self.base+path, headers={'x-api-key':token,'Accept':'application/json'})
        try:
            with build_opener(NoRedirect()).open(request,timeout=3) as response:
                raw = response.read(MAX_BYTES+1)
        except HTTPException:
            raise OSError('Provider transport incomplete') from None
        if len(raw)>MAX_BYTES:
            raise ValueError('Provider response exceeds bound')
        return json.loads(raw)

    def snapshot(self):
        key = quote(self.config['project'],safe='')
        p = self.get('/projects/'+key)
        board = self.get('/projects/'+key+'/issues/board')
        field = next(f['id'] for f in p['customFields'] if f['name']==self.config.get('field','Project Intent v0'))
        records = []
        for issue in board['issues']:
            values = [v['value'] for v in issue['fieldValues'] if v['fieldId']==field and v['value']]
            if not values: continue
            record = json.loads(values[0])
            record.update(title=issue['title'],provider_id=issue['id'],initiative_id=issue.get('initiativeId'))
            record['provider_identifier']=issue.get('identifier')
            column=next((c for c in p.get('columns',[]) if c['id']==issue.get('columnId')),None)
            record['provider_lifecycle']=column['name'] if column else None
            for role in ('delegate','assignee'):
                user_id=issue.get(role+'UserId')
                member=next((m for m in p.get('assignees',[]) if m['userId']==user_id),None)
                record[role+'_name']=member.get('name') if member else None
                record[role+'_username']=member.get('username') if member else None
            # Only configured trusted provider URL, not user-supplied links.
            record['provider_url'] = self.config.get('web_url','')
            records.append(record)
        # Paging applies to native initiatives. A failed page invalidates refresh.
        initiatives=[]; page=1
        while True:
            result=self.get('/projects/'+key+'/initiatives?limit=100&page='+str(page))
            rows=result.get('data', result.get('items', []))
            initiatives.extend(rows)
            total=result.get('total',result.get('pagination',{}).get('total',len(initiatives)))
            if len(initiatives)>=total: break
            if not rows:raise ValueError('Incomplete initiative refresh')
            page+=1
            if page>20: raise ValueError('Initiative page limit')
        return validate_snapshot({'version':1,'mission':p['project']['description'] or p['project']['name'],
            'records':records,'initiatives':initiatives,'source':{'provider':'itsaplan','project':self.config['project'],
            'captured_at':utcnow().isoformat(),'authoritative':False,'mode':'offline_snapshot'}})


class SnapshotProvider:
    """Offline adapter also proves consumers do not depend on It's a Plan."""
    capabilities = ('read-snapshot',)

    def __init__(self,config): self.path=Path(config['path'])

    def snapshot(self): return validate_snapshot(json.loads(self.path.read_text()))


def adapter(config):
    kinds={'itsaplan':ItsAPlan,'snapshot':SnapshotProvider}
    if config.get('kind') not in kinds: raise ValueError('Unsupported provider adapter')
    return kinds[config['kind']](config)
