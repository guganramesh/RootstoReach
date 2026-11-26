from app import app, db
from models import User
import sys

errors = []

with app.app_context():
    with app.test_request_context('/'):
        from flask import render_template_string
        try:
            r = render_template_string('{{ get_img_url("default_avatar.png","FB") }}')
            print('context_processor get_img_url: OK ->', r)
        except Exception as e:
            errors.append(f'context_processor: {e}')

        # Test all routes render without errors
        routes_to_test = [
            ('/', {}),
            ('/knowledge-hub', {}),
            ('/marketplace', {}),
            ('/about', {}),
            ('/contact', {}),
        ]
        client = app.test_client()
        for url, _ in routes_to_test:
            resp = client.get(url)
            status = 'OK' if resp.status_code == 200 else f'FAIL({resp.status_code})'
            print(f'GET {url}: {status}')

        # Test authenticated routes with session
        with client.session_transaction() as sess:
            sess['user_id'] = 2  # Ramesh Kumar

        for url in ['/dashboard', '/settings', '/profile/2', '/messages', '/my-knowledge', '/orders']:
            resp = client.get(url)
            status = 'OK' if resp.status_code == 200 else f'FAIL({resp.status_code})'
            print(f'GET {url} (auth): {status}')
            if resp.status_code == 500:
                errors.append(f'{url}: 500 error')

if errors:
    print('\nERRORS FOUND:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
else:
    print('\nAll routes OK!')
