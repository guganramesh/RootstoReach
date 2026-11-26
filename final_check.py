from app import app, db
from models import User, Product, KnowledgePost, Order, Conversation, Message, ContactMessage, Notification

with app.app_context():
    client = app.test_client()

    # Test /uploads/ route works for existing file
    resp = client.get('/uploads/20260613231007_Logo_Landscape.png')
    print(f'GET /uploads/file.png: {"OK (200)" if resp.status_code==200 else f"FAIL({resp.status_code})"}')

    # Test /uploads/ for nonexistent file
    resp = client.get('/uploads/nonexistent.png')
    print(f'GET /uploads/nonexistent.png: {"OK (404)" if resp.status_code==404 else f"UNEXPECTED({resp.status_code})"}')

    # Session with user who HAS uploaded avatar
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Admin (has uploaded file)

    resp = client.get('/settings')
    print(f'GET /settings (user with avatar): {"OK" if resp.status_code==200 else f"FAIL({resp.status_code})"}')

    resp = client.get('/profile/1')
    print(f'GET /profile/1 (admin with avatar): {"OK" if resp.status_code==200 else f"FAIL({resp.status_code})"}')

    # Check avatar URL appears in response HTML
    html = resp.data.decode('utf-8')
    has_upload_url = '/uploads/20260613231007_Logo_Landscape.png' in html
    print(f'Profile shows uploaded avatar URL: {"YES" if has_upload_url else "NO (using fallback)"}')

    print()
    print('=== DATABASE SUMMARY ===')
    print(f'Users: {User.query.count()}')
    print(f'Knowledge Posts: {KnowledgePost.query.count()}')
    print(f'Products: {Product.query.count()}')
    print(f'Orders: {Order.query.count()}')
    print(f'Conversations: {Conversation.query.count()}')
    print(f'Messages: {Message.query.count()}')
    print(f'Contact Messages: {ContactMessage.query.count()}')
    print(f'Notifications: {Notification.query.count()}')
    print()
    print('=== DEMO ACCOUNTS ===')
    for u in User.query.all():
        pwd = 'admin123' if u.role=='admin' else 'farmer123' if u.role=='farmer' else 'buyer123'
        print(f'  [{u.role.upper()}] {u.email} / {pwd}')
