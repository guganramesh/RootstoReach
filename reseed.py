from app import app, db
from models import User, KnowledgePost, Product, Order, Conversation, Message, ContactMessage, Notification

with app.app_context():
    # Drop and recreate all tables
    db.drop_all()
    db.create_all()
    print('Tables reset')

    from app import seed_data
    seed_data()

    print('Users:', User.query.count())
    print('Knowledge Posts:', KnowledgePost.query.count())
    print('Products:', Product.query.count())
    print('Orders:', Order.query.count())
    print('Conversations:', Conversation.query.count())
    print('Messages:', Message.query.count())
    print('Contact Messages:', ContactMessage.query.count())
    print('Notifications:', Notification.query.count())
    print()
    print('--- Sample Users ---')
    for u in User.query.all():
        print(f'  {u.id}. {u.full_name} | {u.email} | {u.role}')
    print()
    print('--- Sample Conversations ---')
    for c in Conversation.query.all():
        print(f'  Conv {c.id}: {c.user1.full_name} <-> {c.user2.full_name} ({len(c.messages)} messages)')
