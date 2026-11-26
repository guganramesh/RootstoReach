from app import app, db
from models import User

with app.app_context():
    with app.test_request_context('/'):
        from flask import render_template_string
        r1 = render_template_string('{{ get_img_url("default_avatar.png", "FALLBACK") }}')
        print('Default avatar:', r1)
        r2 = render_template_string('{{ get_img_url("20260613210141_Logo.png", "FALLBACK") }}')
        print('Uploaded file:', r2)
        r3 = render_template_string('{{ get_img_url(none, "FALLBACK_NONE") }}')
        print('None filename:', r3)
        print('All OK - context_processor is working')
