"""Opt-in local integration smoke test. Creates a clearly labelled test account and PDFs."""
import json
import tempfile
import time
import uuid
from pathlib import Path
import httpx
import fitz
from app.db.postgres import SessionLocal
from app.models.document import User
from app.core.security import hash_password

state_path = Path(tempfile.gettempdir()) / 'acamind-local-smoke.json'
password = uuid.uuid4().hex
email = f'acamind-smoke-{int(time.time())}@example.test'
with SessionLocal() as db:
    user = User(id=uuid.uuid4(), email=email, hashed_password=hash_password(password),
                full_name='Acamind Local Smoke Test', role='student', plan='free')
    db.add(user); db.commit()

client = httpx.Client(base_url='http://127.0.0.1:8001/api/v1', timeout=240, trust_env=False)
def request(method, path, expected=200, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(f'{path}: HTTP {response.status_code}: {response.text[:400]}')
    return response.json()

login = request('POST', '/auth/login', json={'email': email, 'password': password})
client.headers['Authorization'] = 'Bearer ' + login['access_token']
state = {'email': email, 'password': password, 'token': login['access_token'], 'documents': []}
state_path.write_text(json.dumps(state), encoding='utf-8')
print('PASS login', flush=True)
pdfs = []
for index in range(2):
    pdf = fitz.open()
    page = pdf.new_page()
    text = f'''Acamind Synthetic Study of Student Wellbeing Version {index + 1}
This is synthetic test data, not a real scientific publication.
Our objective was to evaluate student wellbeing after a structured intervention.
Our randomized study design compared a support program against a waitlist control.
Our sample included {100 + index * 20} adult university students recruited locally.
We collected questionnaire data at baseline and after twelve weeks of follow-up.
Our measurement instrument was the synthetic wellbeing scale with a range of 0 to 100.
Higher scores indicate better wellbeing and no items were reverse coded.
Our results showed an increase of {5 + index} points relative to the control group.
Our limitations include a small sample and recruitment from only one university.
These results should not be generalized beyond the sampled population.
The intervention consisted of weekly group sessions delivered over twelve weeks.
We used an intention to treat analysis with baseline scores as a covariate.
'''
    page.insert_textbox(fitz.Rect(50, 50, 550, 780), text, fontsize=12)
    pdf.set_metadata({'title': f'Acamind Synthetic Study of Student Wellbeing Version {index+1}', 'author': 'Synthetic Test Team'})
    data = pdf.tobytes(); pdf.close(); pdfs.append(data)
    result = request('POST', '/document/upload', files={'file': ('acamind-smoke-same-name.pdf', data, 'application/pdf')})
    state['documents'].append(result['document_id'])
    state_path.write_text(json.dumps(state), encoding='utf-8')
assert len(set(state['documents'])) == 2
print('PASS different PDF content with same filename retained separately', flush=True)
duplicate = request('POST', '/document/upload', files={'file': ('renamed-smoke.pdf', pdfs[0], 'application/pdf')})
assert duplicate['document_id'] == state['documents'][0]
print('PASS identical content deduplicated', flush=True)
second = state['documents'][1]
cancel = client.post(f'/document/{second}/cancel-processing')
print('Cancel request:', cancel.status_code, flush=True)
deadline = time.monotonic() + 240
last = None
while time.monotonic() < deadline:
    statuses = [request('GET', f'/document/{did}/processing') for did in state['documents']]
    snapshot = [(r['status'], r['stage']) for r in statuses]
    if snapshot != last:
        print('Processing:', snapshot, flush=True); last = snapshot
    if all(r['status'] in ('ready', 'error', 'cancelled') for r in statuses):
        break
    time.sleep(2)
if statuses[1]['status'] == 'cancelled':
    time.sleep(.5)
    request('POST', f'/document/{second}/retry-processing')
    print('PASS cancelled task retried from stored PDF', flush=True)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        status = request('GET', f'/document/{second}/processing')
        if status['status'] in ('ready', 'error'):
            break
        time.sleep(2)
for did in state['documents']:
    status = request('GET', f'/document/{did}/processing')
    assert status['status'] == 'ready', status
print('PASS both PDFs indexed with actual embedding model', flush=True)
profiles = [request('GET', f'/features/study-profile/{did}') for did in state['documents']]
for profile in profiles:
    assert profile['fields']['sample']['candidates']
print('PASS study profiles with source candidates', flush=True)
did = state['documents'][0]
c = profiles[0]['fields']['sample']['candidates'][0]
body = {'expected_revision': 0, 'status': 'confirmed', 'value': '100 adult university students',
        'note': 'Local synthetic smoke test', 'chunk_id': c['chunk_id'], 'quote': c['quote']}
request('POST', f'/features/study-profile/{did}/reviews/sample', json=body)
request('POST', f'/features/study-profile/{did}/reviews/sample', expected=409, json=body)
history = request('GET', f'/features/study-profile/{did}/reviews/sample')
assert len(history['items']) == 1
print('PASS persisted review, history and stale revision rejection', flush=True)
pairs = request('POST', '/features/study-duplicates', json={'document_ids': state['documents']})
assert pairs['pairs']
print('PASS related version candidates', flush=True)
gap = request('POST', f'/features/study-profile/{did}/search-gap', json={'criterion': 'sample', 'focus': 'university students'})
assert gap['candidates']
assert all(c.get('ranking') for c in gap['candidates'])
print('PASS real retrieval and ranking explanations; sources=' + str([c['ranking']['score_source'] for c in gap['candidates']]), flush=True)
comparison = request('POST', '/features/study-comparability', json={'document_a': did, 'document_b': second, 'focus': 'wellbeing score after twelve weeks'})
print('PASS local-model comparability: ' + comparison['status'], flush=True)
relations = request('POST', '/features/study-relations', json={'document_a': did, 'document_b': second, 'focus': 'wellbeing score after twelve weeks'})
print('PASS local-model relations: ' + relations['status'], flush=True)
print('SMOKE COMPLETE', flush=True)
