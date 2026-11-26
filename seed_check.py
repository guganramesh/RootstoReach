from app import app, db, seed_data
from models import User, KnowledgePost, Product, Order, Conversation, Message, ContactMessage, Notification

with app.app_context():
    db.create_all()
    seed_data()
    print('Users:', User.query.count())
    print('Knowledge Posts:', KnowledgePost.query.count())
    print('Products:', Product.query.count())
    print('Orders:', Order.query.count())
    print('Conversations:', Conversation.query.count())
    print('Messages:', Message.query.count())
    print('Contact Messages:', ContactMessage.query.count())
    print('Notifications:', Notification.query.count())
