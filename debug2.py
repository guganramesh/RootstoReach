from app import app, db, get_img_url
from models import User, Product

with app.app_context():
    with app.test_request_context('/'):
        fallbacks = ['https://img1.jpg','https://img2.jpg','https://img3.jpg']
        print('=== Avatar test ===')
        for u in User.query.all():
            idx = u.id % len(fallbacks)
            r1 = get_img_url(u.avatar, fallbacks[idx])
            r2 = get_img_url(u.avatar, '')
            print(f'  User {u.id} avatar={u.avatar!r} | with_fallback={r1[:30]} | empty_fallback={r2!r}')

        print('=== Product image test ===')
        prod_imgs = ['https://p1.jpg','https://p2.jpg','https://p3.jpg']
        for p in Product.query.all():
            idx = p.id % len(prod_imgs)
            r = get_img_url(p.image, prod_imgs[idx])
            print(f'  Product {p.id} image={p.image!r} -> {r[:30]}')
        print('ALL OK')
