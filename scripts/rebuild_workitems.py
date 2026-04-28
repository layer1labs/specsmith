import json,os
req_path='.specsmith/requirements.json'
with open(req_path,encoding='utf-8') as f:
    reqs=json.load(f)
# load testcases
with open('.specsmith/testcases.json',encoding='utf-8') as f:
    tests=json.load(f)
# load config
config={}
if os.path.exists('.specsmith/config.yml'):
    with open('.specsmith/config.yml',encoding='utf-8') as f:
        import yaml
        config=yaml.safe_load(f)
max_attempts=config.get('max_attempts',3) if config else 3
workitems=[]
# map requirement ids to test case ids
req_to_tests={}
for t in tests:
    req_to_tests.setdefault(t['requirement_id'],[]).append(t['id'])
for i,req in enumerate(reqs,1):
    wid=f'WORK-{i:03d}'
    priority=req.get('priority','high')
    workitems.append({
        "id":wid,
        "requirement_id":req['id'],
        "test_case_ids":req_to_tests.get(req['id'],[]),
        "status":"pending",
        "attempts":0,
        "max_attempts":max_attempts,
        "priority":priority
    })
with open('.specsmith/workitems.json','w',encoding='utf-8') as f:
    json.dump(workitems,f,indent=2)
print('Rebuilt',len(workitems),'work items')
