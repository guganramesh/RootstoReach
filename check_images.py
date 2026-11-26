from app import app, db, get_img_url
from models import User, Product

with app.app_context():
    with app.test_request_context('/'):
        print('=== USER AVATARS ===')
        for user in User.query.all():
            img = get_img_url(user.avatar, 'NO_UPLOAD')
            print(f'  User {user.id} ({user.full_name}): {repr(user.avatar)} -> {img}')

        print()
        print('=== PRODUCT IMAGES ===')
        for p in Product.query.all():
            img = get_img_url(p.image, 'NO_UPLOAD')
            print(f'  Product {p.id} ({p.name}): {repr(p.image)} -> {img}')
