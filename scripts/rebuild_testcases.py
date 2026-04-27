import json
import pathlib

# read requirements
with open('.specsmith/requirements.json',encoding='utf-8') as f:
    reqs=json.load(f)

# generate test cases
tests=[]
for i,req in enumerate(reqs,1):
    tid=f'TEST-{i:03d}'
    tests.append({
        "id":tid,
        "title":req.get("Title",req.get("title")),
        "description":req.get("Description",req.get("description")),
        "requirement_id":req['id'],
        "type":"unit",
        "verification_method":"evaluator",
        "input":{} ,
        "expected_behavior":{},
        "confidence":1.0
    })

# write md
md='# Test Specification\n\n'
for t in tests:
    md += f'## {t["id"]}. {t["title"]}\n'
    md += f'- **ID:** {t["id"]}\n'
    md += f'- **Title:** {t["title"]}\n'
    md += f'- **Description:** {t["description"]}\n'
    md += f'- **Requirement ID:** {t["requirement_id"]}\n'
    md += f'- **Type:** {t["type"]}\n'
    md += f'- **Verification Method:** {t["verification_method"]}\n'
    md += f'- **Input:** {t["input"]}\n'
    md += f'- **Expected Behavior:** {t["expected_behavior"]}\n'
    md += f'- **Confidence:** {t["confidence"]}\n\n'
with open('TEST_SPEC.md','w',encoding='utf-8') as f:
    f.write(md)

with open('.specsmith/testcases.json','w',encoding='utf-8') as f:
    json.dump(tests,f,indent=2)

print('Rebuilt',len(tests),'test cases')
