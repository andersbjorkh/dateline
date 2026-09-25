import json,glob,collections
L=json.load(open('.cache/sitelinks.json'))
days={f[-10:-5]:json.load(open(f)) for f in sorted(glob.glob('.cache/??-??.json'))}
freq=collections.Counter()
def uniq(d):
  seen=set()
  for e in d['selected']+d['events']:
    if e['text'] in seen or e.get('year') is None: continue
    seen.add(e['text']); yield e
for d in days.values():
  for e in uniq(d):
    for q in {p['q'] for p in e['pages'] if p['q']}: freq[q]+=1
def score(e):
  s=[L.get(p['q'],0) for p in e['pages'] if p['q'] and freq[p['q']]<=5]
  return max(s) if s else 0
out={}
for k,d in days.items():
  ev=list(uniq(d)); sel={e['text'] for e in d['selected']}
  ranked=sorted(ev,key=lambda e:-score(e))
  cands=[e for e in ev if e['text'] in sel]
  for e in ranked:
    if len(cands)>=14: break
    if e not in cands: cands.append(e)
  out[k]=[(e['year'],e['text']) for e in cands]
json.dump(out,open('.cache/shortlist.json','w'))
with open('.cache/shortlist.txt','w') as f:
  for k,c in out.items():
    f.write(f'## {k}\n')
    for i,(y,t) in enumerate(c): f.write(f'{i} {y} {t[:100]}\n')
