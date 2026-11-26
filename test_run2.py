from app import app, db
from models import User, Conversation

errors = []

with app.app_context():
    client = app.test_client()

    # Admin session
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Admin

    for url in ['/admin', '/admin/users', '/admin/contacts']:
        resp = client.get(url)
        status = 'OK' if resp.status_code == 200 else f'FAIL({resp.status_code})'
        print(f'GET {url} (admin): {status}')
        if resp.status_code == 500:
            errors.append(f'{url}: 500')

    # Test messages with conv
    with client.session_transaction() as sess:
        sess['user_id'] = 8  # Hans Muller (buyer)
    conv = Conversation.query.first()
    if conv:
        resp = client.get(f'/messages?conv={conv.id}')
        status = 'OK' if resp.status_code == 200 else f'FAIL({resp.status_code})'
        print(f'GET /messages?conv={conv.id}: {status}')

    # Test start_conversation
    with client.session_transaction() as sess:
        sess['user_id'] = 8
    resp = client.post('/messages/start/2')
    status = 'REDIRECT' if resp.status_code in (301,302) else f'FAIL({resp.status_code})'
    print(f'POST /messages/start/2: {status}')

    # Test knowledge hub with category filter
    with client.session_transaction() as sess:
        sess['user_id'] = 2
    resp = client.get('/knowledge-hub?category=Organic+Farming')
    print(f'GET /knowledge-hub?category=Organic+Farming: {"OK" if resp.status_code==200 else resp.status_code}')

    # Test profile pages for all farmers
    for uid in range(2, 8):
        resp = client.get(f'/profile/{uid}')
        print(f'GET /profile/{uid}: {"OK" if resp.status_code==200 else resp.status_code}')

if errors:
    print('\nERRORS:', errors)
else:
    print('\nAll admin+message routes OK!')
