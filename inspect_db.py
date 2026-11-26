from app import app, db
from models import User, KnowledgePost, Product, Order
from sqlalchemy import inspect as sa_inspect

with app.app_context():
    insp = sa_inspect(db.engine)
    print("=== DB FILE: roots_to_reach.db ===")
    print("TABLES:", insp.get_table_names())
    print()

    users = User.query.all()
    print(f"=== USERS ({len(users)} total) ===")
    for u in users:
        print(f"  ID:{u.id} | {u.full_name} | {u.email} | Role:{u.role} | Active:{u.is_active} | PwdHash:{u.password_hash[:30]}...")
    print()

    posts = KnowledgePost.query.all()
    print(f"=== KNOWLEDGE POSTS ({len(posts)} total) ===")
    for k in posts:
        print(f"  ID:{k.id} | {k.title} | Category:{k.category} | Views:{k.views} | Author:{k.author.full_name}")
    print()

    prods = Product.query.all()
    print(f"=== PRODUCTS ({len(prods)} total) ===")
    for p in prods:
        print(f"  ID:{p.id} | {p.name} | Rs{p.price}/{p.unit} | Stock:{p.stock} | Seller:{p.seller.full_name}")
    print()

    orders = Order.query.all()
    print(f"=== ORDERS ({len(orders)} total) ===")
    for o in orders:
        print(f"  ID:{o.id} | {o.product.name} | Qty:{o.quantity} | Status:{o.status} | Amount:Rs{o.total_amount}")
