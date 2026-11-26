from app import app, db
from models import User, Product

errors = []
with app.app_context():
    client = app.test_client()

    # Login as Ramesh (farmer, id=2)
    with client.session_transaction() as sess:
        sess['user_id'] = 2

    for url in ['/profile/2', '/settings', '/product/1', '/product/2', '/product/3']:
        try:
            resp = client.get(url)
            if resp.status_code == 500:
                print(f'FAIL 500: {url}')
                # print response data for debug
                print(resp.data[:2000].decode('utf-8', errors='replace'))
                errors.append(url)
            else:
                print(f'OK {resp.status_code}: {url}')
        except Exception as e:
            print(f'EXCEPTION {url}: {e}')
            errors.append(url)

print('\nFailed routes:', errors)
