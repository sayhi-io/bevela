"""Bounded context/thinking check against an already-admitted Qwen endpoint.

No worker dispatch or model lifecycle mutation. Store only configuration/usage and
probe outcome, not model reasoning text. This is not an A/B result.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.request
from urllib.parse import urlparse


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Refusing to overwrite preflight evidence')
    origin=urlparse(args.endpoint)
    if origin.scheme not in ('http','https') or origin.username or origin.password:
        parser.error('Expected a credential-free admitted endpoint URL')
    base=args.endpoint.rstrip('/').removesuffix('/v1')
    def call(path,body=None):
        request=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),
                                      headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=1800) as r:return json.load(r)
    info=call('/get_server_info')
    context=info.get('context_length')
    assert isinstance(context,int) and context>=100000, 'Serving context below requested minimum'
    text=('The first marker is AMBER-ORCHARD. Read the final instruction after the padding.\n'
          +'neutral '*100500
          +'\nThe last marker is COBALT-HARBOR. Return exactly the first marker, a space, then the last marker.')
    messages=[{'role':'user','content':text}]
    common={'model':args.model,'messages':messages,'reasoning_effort':'xhigh',
            'chat_template_kwargs':{'enable_thinking':True}}
    tokens=call('/tokenize',common)
    token_count=tokens.get('count',tokens.get('token_count'))
    if token_count is None and isinstance(tokens.get('token_ids'),list):
        token_count=len(tokens['token_ids'])
    assert isinstance(token_count,int) and 100000<=token_count<context-8192, ('Unexpected token count',token_count)
    started=time.monotonic()
    response=call('/v1/chat/completions',{**common,'max_completion_tokens':8192,'stream':False})
    message=response['choices'][0]['message']
    reasoning=message.get('reasoning_content') or message.get('reasoning') or ''
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'endpoint':args.endpoint,
            'model':args.model,'serving_context_length':context,'tokenized_prompt':token_count,
            'requested_thinking':True,'requested_reasoning_effort':'xhigh',
            'reasoning_parser':info.get('reasoning_parser'),'reasoning_characters':len(reasoning),
            'effort_semantics':'Tokenizer template accepts xhigh/medium/low, rejects high; scaling not independently established',
            'usage':response.get('usage'),'finish_reason':response['choices'][0].get('finish_reason'),
            'marker_retrieval_passed':message.get('content','').strip()=='AMBER-ORCHARD COBALT-HARBOR',
            'elapsed_seconds':round(time.monotonic()-started,3),'study_result':False}
    result['passed']=(result['marker_retrieval_passed'] and len(reasoning)>0
                      and response.get('usage',{}).get('prompt_tokens',0)>=100000)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
