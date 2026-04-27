import json
with open('.specsmith/requirements.json') as f:
    data=json.load(f)
print('count',len(data))
print('first',data[0]['id'])
print('last',data[-1]['id'])
ids={d['id'] for d in data}
missing=[f'REQ-{i:03d}' for i in range(1,65) if f'REQ-{i:03d}' not in ids]
print('missing',missing)
# duplicates check
from collections import Counter
cnt=Counter(d['id'] for d in data)
dup=[k for k,v in cnt.items() if v>1]
print('duplicates',dup)
