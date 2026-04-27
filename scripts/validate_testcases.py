import json,os
# Load requirements
with open('.specsmith/requirements.json',encoding='utf-8') as f:
    reqs=json.load(f)
# Load tests
with open('.specsmith/testcases.json',encoding='utf-8') as f:
    tests=json.load(f)
ids=[t['id'] for t in tests]
miss=[f'TEST-{i:03d}' for i in range(1,65) if f'TEST-{i:03d}' not in ids]
dup=[x for x in ids if ids.count(x)>1]
# Check each requirement has a test
req_ids=[r['id'] for r in reqs]
untested=[r for r in req_ids if r not in [t['requirement_id'] for t in tests]]
# Validate links valid
link_errors=[t['requirement_id'] for t in tests if t['requirement_id'] not in req_ids]
# Validate markdown contains 64 headings
headings=0
with open('TEST_SPEC.md','r',encoding='utf-8') as f:
    for line in f:
        if line.startswith('## '):
            headings+=1
print('test count',len(tests))
print('first ID',tests[0]['id'])
print('last ID',tests[-1]['id'])
print('missing IDs',miss)
print('duplicate IDs',dup)
print('untested requirements',untested)
print('invalid requirement links',link_errors)
print('markdown headings',headings)
