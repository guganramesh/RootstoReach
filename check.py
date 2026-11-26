from app import app, db
from models import User, Product, ContactMessage
from sqlalchemy import inspect as sa_inspect

with app.app_context():
    insp = sa_inspect(db.engine)
    print('TABLES:', insp.get_table_names())
    u = User.query.get(2)
    print('Ramesh avatar:', u.avatar)
    p = Product.query.get(9)
    print('Product 9 image:', p.image)
    from app import get_img_url
    with app.test_request_context():
        print('Avatar URL:', get_img_url(u.avatar, 'FALLBACK_UNSPLASH'))
        print('Product URL:', get_img_url(p.image, 'FALLBACK_UNSPLASH'))
    print('ContactMessage table exists:', ContactMessage.query.count(), 'rows')
