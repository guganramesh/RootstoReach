import os
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort, send_from_directory)
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# ── import models AFTER app is configured ──
from models import db, User, KnowledgePost, Product, Order, Conversation, Message, Notification, ContactMessage

db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── Helpers ────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_file(file):
    """Save uploaded file and return filename, or None if failed"""
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        return None
    
    try:
        filename = secure_filename(file.filename)
        if not filename:
            return None
            
        # Add timestamp prefix to avoid conflicts
        ts = datetime.now().strftime('%Y%m%d%H%M%S_')
        filename = ts + filename
        
        # Ensure upload folder exists
        upload_path = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        full_path = os.path.join(upload_path, filename)
        file.save(full_path)
        
        return filename
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def get_img_url(filename, fallback_url):
    """Returns the real upload path if file exists, else fallback URL."""
    defaults = ('default_avatar.png', 'default_knowledge.jpg', 'default_product.jpg', '', None)
    
    # If no filename or it's a default placeholder, return fallback
    if not filename or filename in defaults:
        return fallback_url
    
    # Check if actual uploaded file exists
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return '/uploads/' + filename
    except Exception:
        pass
    
    # Return fallback if file doesn't exist or any error
    return fallback_url

@app.context_processor
def inject_helpers():
    return dict(get_img_url=get_img_url)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        u = current_user()
        if not u or u.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ─── Uploads ────────────────────────────────────────────────────────────────

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── PUBLIC ROUTES ──────────────────────────────────────────────────────────

@app.route('/')
def home():
    posts    = KnowledgePost.query.filter_by(is_published=True).order_by(KnowledgePost.created_at.desc()).limit(6).all()
    products = Product.query.filter_by(is_available=True).limit(8).all()
    farmers  = User.query.filter_by(role='farmer').limit(3).all()
    return render_template('home.html', posts=posts, products=products, farmers=farmers, user=current_user())

@app.route('/about')
def about():
    return render_template('about.html', user=current_user())

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if not all([name, email, message]):
            flash('Please fill all required fields.', 'error')
            return render_template('contact.html', user=current_user())
        cm = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(cm)
        db.session.commit()
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', user=current_user())

@app.route('/knowledge-hub')
def knowledge_hub():
    category = request.args.get('category', 'all')
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    query    = KnowledgePost.query.filter_by(is_published=True)
    if category and category != 'all':
        query = query.filter(KnowledgePost.category.ilike(f'%{category}%'))
    if search:
        query = query.filter(KnowledgePost.title.ilike(f'%{search}%'))
    posts = query.order_by(KnowledgePost.created_at.desc()).paginate(page=page, per_page=9)
    return render_template('knowledge_hub.html', posts=posts, category=category, search=search, user=current_user())

@app.route('/knowledge/<int:post_id>')
def knowledge_detail(post_id):
    post = db.session.get(KnowledgePost, post_id) or abort(404)
    post.views += 1
    db.session.commit()
    related = KnowledgePost.query.filter(
        KnowledgePost.category == post.category,
        KnowledgePost.id != post.id
    ).limit(3).all()
    u = current_user()
    is_owner = u is not None and u.id == post.user_id
    return render_template('knowledge_detail.html', post=post, related=related, user=u, is_owner=is_owner)

@app.route('/knowledge/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_knowledge(post_id):
    post = db.session.get(KnowledgePost, post_id) or abort(404)
    if post.user_id != session['user_id']:
        abort(403)
    user = current_user()
    if request.method == 'POST':
        post.title       = request.form.get('title', '').strip() or post.title
        post.category    = request.form.get('category', '').strip() or post.category
        post.description = request.form.get('description', '').strip() or post.description
        post.steps       = request.form.get('steps', '').strip()
        post.tips        = request.form.get('tips', '').strip()
        post.materials   = request.form.get('materials', '').strip()
        new_img = save_file(request.files.get('image'))
        if new_img:
            post.image = new_img
        db.session.commit()
        flash('Knowledge post updated!', 'success')
        return redirect(url_for('knowledge_detail', post_id=post.id))
    return render_template('edit_knowledge.html', post=post, user=user)

@app.route('/marketplace')
def marketplace():
    category = request.args.get('category', 'all')
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    query    = Product.query.filter_by(is_available=True)
    if category and category != 'all':
        query = query.filter(Product.category.ilike(f'%{category}%'))
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=8)
    user = current_user()
    current_user_id = user.id if user else None
    return render_template('marketplace.html', products=products, category=category, search=search, user=user, current_user_id=current_user_id)

@app.route('/my-products')
@login_required
def my_products():
    user     = current_user()
    products = Product.query.filter_by(seller_id=user.id).order_by(Product.created_at.desc()).all()
    return render_template('my_products.html', user=user, products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    related = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id,
        Product.is_available == True
    ).limit(4).all()
    user = current_user()
    is_owner = user is not None and user.id == product.seller_id
    return render_template('product_detail.html', product=product, related=related, user=user, is_owner=is_owner, current_user_id=user.id if user else None)

# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        phone     = request.form.get('phone', '').strip()
        location  = request.form.get('location', '').strip()
        skills    = request.form.get('skills', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        if not all([full_name, email, password]):
            flash('Please fill all required fields.', 'error')
            return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')
        user = User(full_name=full_name, email=email, phone=phone, location=location, skills=skills)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        flash(f'Welcome to Roots to Reach, {full_name}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('login.html')
            session['user_id'] = user.id
            session.permanent = 'remember_me' in request.form
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(
        Notification.created_at.desc()).limit(5).all()
    recent_orders = Order.query.filter_by(seller_id=user.id).order_by(
        Order.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', user=user,
                           notifications=notifications, recent_orders=recent_orders)

# ─── KNOWLEDGE ───────────────────────────────────────────────────────────────

@app.route('/share-knowledge', methods=['GET', 'POST'])
@login_required
def share_knowledge():
    user = current_user()
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        category    = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        steps       = request.form.get('steps', '').strip()
        tips        = request.form.get('tips', '').strip()
        materials   = request.form.get('materials', '').strip()
        if not all([title, category, description]):
            flash('Title, category, and description are required.', 'error')
            return render_template('share_knowledge.html', user=user)
        image_name = save_file(request.files.get('image')) or 'default_knowledge.jpg'
        post = KnowledgePost(title=title, category=category, description=description,
                              steps=steps, tips=tips, materials=materials,
                              image=image_name, user_id=user.id)
        db.session.add(post)
        db.session.add(Notification(user_id=user.id,
                                    message=f'Your knowledge "{title}" was published!',
                                    type='success', time_ago='just now'))
        db.session.commit()
        flash('Knowledge shared successfully!', 'success')
        return redirect(url_for('my_knowledge'))
    return render_template('share_knowledge.html', user=user)

@app.route('/my-knowledge')
@login_required
def my_knowledge():
    user  = current_user()
    posts = KnowledgePost.query.filter_by(user_id=user.id).order_by(KnowledgePost.created_at.desc()).all()
    return render_template('my_knowledge.html', user=user, posts=posts)

@app.route('/knowledge/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_knowledge(post_id):
    post = db.session.get(KnowledgePost, post_id) or abort(404)
    if post.user_id != session['user_id']:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Knowledge post deleted.', 'info')
    return redirect(url_for('my_knowledge'))

# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    if product.seller_id != session['user_id']:
        abort(403)
    user = current_user()
    if request.method == 'POST':
        product.name        = request.form.get('name', '').strip() or product.name
        product.category    = request.form.get('category', '').strip() or product.category
        product.description = request.form.get('description', '').strip()
        product.price       = float(request.form.get('price') or product.price)
        product.unit        = request.form.get('unit', product.unit)
        product.stock       = int(request.form.get('stock') or product.stock)
        new_img = save_file(request.files.get('image'))
        if new_img:
            product.image = new_img
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))
    return render_template('edit_product.html', product=product, user=user)

@app.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    if product.seller_id != session['user_id']:
        abort(403)
    Order.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('marketplace'))

@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    user = current_user()
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        category    = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        price       = request.form.get('price', 0)
        unit        = request.form.get('unit', 'kg')
        stock       = request.form.get('stock', 0)
        if not all([name, category, price]):
            flash('Name, category, and price are required.', 'error')
            return render_template('add_product.html', user=user)
        image_name = save_file(request.files.get('image')) or 'default_product.jpg'
        product = Product(name=name, category=category, description=description,
                          price=float(price), unit=unit, stock=int(stock),
                          image=image_name, seller_id=user.id)
        db.session.add(product)
        db.session.commit()
        flash('Product listed successfully!', 'success')
        return redirect(url_for('marketplace'))
    return render_template('add_product.html', user=user)

# ─── ORDERS ──────────────────────────────────────────────────────────────────

@app.route('/order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    product  = db.session.get(Product, product_id) or abort(404)
    user     = current_user()
    quantity = int(request.form.get('quantity', 1))
    if product.seller_id == user.id:
        flash('You cannot order your own product.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    order = Order(product_id=product.id, buyer_id=user.id, seller_id=product.seller_id,
                  quantity=quantity, total_amount=product.price * quantity)
    db.session.add(order)
    db.session.add(Notification(user_id=product.seller_id,
                                message=f'New order received for {product.name}.',
                                type='order', time_ago='just now'))
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user   = current_user()
    status = request.args.get('status', 'all')
    my_q   = Order.query.filter_by(buyer_id=user.id)
    rec_q  = Order.query.filter_by(seller_id=user.id)
    if status != 'all':
        my_q  = my_q.filter_by(status=status)
        rec_q = rec_q.filter_by(status=status)
    my_orders       = my_q.order_by(Order.created_at.desc()).all()
    received_orders = rec_q.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', user=user, my_orders=my_orders,
                           received_orders=received_orders, status=status)

@app.route('/order/update/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    if order.seller_id != session['user_id']:
        abort(403)
    new_status = request.form.get('status')
    if new_status in ['pending', 'placed', 'shipped', 'delivered', 'completed']:
        order.status     = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Order status updated.', 'success')
    return redirect(url_for('orders'))

# ─── MESSAGES ────────────────────────────────────────────────────────────────

@app.route('/messages/start/<int:other_id>', methods=['POST'])
@login_required
def start_conversation(other_id):
    user = current_user()
    if user.id == other_id:
        flash('You cannot message yourself.', 'error')
        return redirect(url_for('messages'))
    other = db.session.get(User, other_id)
    if not other:
        abort(404)
    conv = Conversation.query.filter(
        ((Conversation.user1_id == user.id) & (Conversation.user2_id == other_id)) |
        ((Conversation.user1_id == other_id) & (Conversation.user2_id == user.id))
    ).first()
    if not conv:
        conv = Conversation(user1_id=user.id, user2_id=other_id)
        db.session.add(conv)
        db.session.commit()
    return redirect(url_for('messages', conv=conv.id))

@app.route('/messages')
@login_required
def messages():
    user     = current_user()
    conv_id  = request.args.get('conv', type=int)
    conversations = Conversation.query.filter(
        (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    active_conv   = None
    chat_messages = []
    if conv_id:
        active_conv = db.session.get(Conversation, conv_id)
        if active_conv:
            chat_messages = Message.query.filter_by(conversation_id=conv_id)\
                                         .order_by(Message.created_at).all()
            Message.query.filter_by(conversation_id=conv_id)\
                         .filter(Message.sender_id != user.id)\
                         .update({'is_read': True})
            db.session.commit()
    # list of all other users to start new chat with
    all_users = User.query.filter(User.id != user.id, User.is_active == True).all()
    return render_template('messages.html', user=user, conversations=conversations,
                           active_conv=active_conv, chat_messages=chat_messages,
                           all_users=all_users)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    user    = current_user()
    conv_id = request.form.get('conversation_id', type=int)
    content = request.form.get('content', '').strip()
    if not content or not conv_id:
        return redirect(url_for('messages'))
    conv = db.session.get(Conversation, conv_id)
    if not conv:
        abort(404)
    db.session.add(Message(conversation_id=conv_id, sender_id=user.id, content=content))
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('messages', conv=conv_id))

# ─── PROFILE & SETTINGS ──────────────────────────────────────────────────────

@app.route('/profile/<int:user_id>')
def profile(user_id):
    profile_user = db.session.get(User, user_id)
    if not profile_user:
        abort(404)
    posts    = KnowledgePost.query.filter_by(user_id=profile_user.id, is_published=True).limit(6).all()
    products = Product.query.filter_by(seller_id=profile_user.id, is_available=True).limit(6).all()
    return render_template('profile.html', farmer=profile_user, posts=posts,
                           products=products, user=current_user())

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = current_user()
    if not user:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            try:
                user.full_name = request.form.get('full_name', user.full_name).strip()
                user.location  = request.form.get('location', user.location or '').strip()
                user.bio       = request.form.get('bio', user.bio or '').strip()
                user.skills    = request.form.get('skills', user.skills or '').strip()
                user.phone     = request.form.get('phone', user.phone or '').strip()
                
                avatar = request.files.get('avatar')
                if avatar and avatar.filename and allowed_file(avatar.filename):
                    avatar_filename = save_file(avatar)
                    if avatar_filename:
                        user.avatar = avatar_filename
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error updating profile. Please try again.', 'error')
                
        elif action == 'change_password':
            current_pw = request.form.get('current_password')
            new_pw     = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')
            
            if not user.check_password(current_pw):
                flash('Current password is incorrect.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            elif len(new_pw) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                try:
                    user.set_password(new_pw)
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('Error changing password. Please try again.', 'error')
                    
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=user)

@app.route('/api/notifications')
@login_required
def api_notifications():
    user  = current_user()
    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({'count': count})

# ─── ADMIN ───────────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    user = current_user()
    stats = {
        'users':    User.query.count(),
        'posts':    KnowledgePost.query.count(),
        'products': Product.query.count(),
        'orders':   Order.query.count(),
        'messages': ContactMessage.query.count()
    }
    users        = User.query.order_by(User.created_at.desc()).limit(10).all()
    contact_msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', user=user, stats=stats,
                           users=users, contact_msgs=contact_msgs)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    user  = current_user()
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', user=user, users=users)

@app.route('/admin/user/toggle/<int:uid>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user(uid):
    u = db.session.get(User, uid) or abort(404)
    u.is_active = not u.is_active
    db.session.commit()
    flash(f'User {"activated" if u.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/contacts')
@login_required
@admin_required
def admin_contacts():
    user = current_user()
    msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contacts.html', user=user, msgs=msgs)

@app.route('/admin/contact/read/<int:msg_id>', methods=['POST'])
@login_required
@admin_required
def admin_mark_read(msg_id):
    cm = db.session.get(ContactMessage, msg_id) or abort(404)
    cm.is_read = True
    db.session.commit()
    return redirect(url_for('admin_contacts'))

# ─── ERROR HANDLERS ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html', user=current_user()), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html', user=current_user()), 403

# ─── SEED DATA ───────────────────────────────────────────────────────────────

def seed_data():
    if User.query.count() > 0:
        return

    # ── Users ──
    admin = User(full_name='Admin', email='admin@rootstoreach.com',
                 location='New Delhi, India', role='admin',
                 skills='Platform Management',
                 bio='Platform administrator of Roots to Reach.')
    admin.set_password('admin123')
    db.session.add(admin)

    farmers_data = [
        ('Ramesh Kumar',  'ramesh@example.com',  '+91-9876543210', 'Punjab, India',
         'Organic Farming, Soil Management, Irrigation',
         'Passionate farmer with 15+ years of experience in organic farming and soil health.'),
        ('Sita Devi',     'sita@example.com',    '+91-9876543211', 'Telangana, India',
         'Organic Farming, Seed Saving, Crop Care',
         'Traditional farmer specializing in heirloom seed preservation and organic methods.'),
        ('Arjun Reddy',   'arjun@example.com',   '+91-9876543212', 'Andhra Pradesh, India',
         'Sustainable Farming, Water Conservation',
         'Expert in sustainable, water-efficient farming with 10 years of drip irrigation experience.'),
        ('Lakshmi Patil', 'lakshmi@example.com', '+91-9876543213', 'Maharashtra, India',
         'Soil Management, Pest Control, Mulching',
         'Specializing in natural pest control and soil enrichment methods without chemicals.'),
        ('Suresh Patel',  'suresh@example.com',  '+91-9876543214', 'Gujarat, India',
         'Irrigation, Crop Rotation, Groundnut Farming',
         'Expert in modern irrigation and groundnut cultivation across 50 acres.'),
        ('Priya Nair',    'priya@example.com',   '+91-9876543215', 'Kerala, India',
         'Spice Farming, Organic Farming, Homestead',
         'Specializing in Kerala spice cultivation — pepper, cardamom, and turmeric.'),
    ]
    farmers = []
    for fd in farmers_data:
        f = User(full_name=fd[0], email=fd[1], phone=fd[2], location=fd[3],
                 skills=fd[4], bio=fd[5], role='farmer')
        f.set_password('farmer123')
        db.session.add(f)
        farmers.append(f)

    buyers_data = [
        ('Hans Muller',    'hans@example.com',    '+49-1234567890', 'Bavaria, Germany',
         'Organic Products Buyer', 'Importing organic produce from India to European markets.'),
        ('John Smith',     'john@example.com',    '+1-5551234567',  'California, USA',
         'Health Food Retailer', 'Sourcing organic spices and grains for US retail chains.'),
        ('Sophie Dubois',  'sophie@example.com',  '+33-612345678',  'Paris, France',
         'Restaurant Owner', 'Buying fresh organic spices for farm-to-table restaurants.'),
        ('Ahmed Khan',     'ahmed@example.com',   '+971-501234567', 'Dubai, UAE',
         'Food Importer', 'Importing premium Indian agricultural products to Gulf markets.'),
    ]
    buyers = []
    for bd in buyers_data:
        b = User(full_name=bd[0], email=bd[1], phone=bd[2], location=bd[3],
                 skills=bd[4], bio=bd[5], role='buyer')
        b.set_password('buyer123')
        db.session.add(b)
        buyers.append(b)

    db.session.flush()

    # ── Knowledge Posts ──
    posts_data = [
        (farmers[0], 'Natural Fertilizer Preparation', 'Organic Farming',
         'Learn how to prepare powerful natural fertilizers from kitchen waste and cow dung to dramatically improve soil fertility without any chemicals.',
         '1. Collect kitchen waste in a container\n2. Mix with equal amount of fresh cow dung\n3. Add water to make a slurry\n4. Stir well and cover loosely\n5. Let it ferment for 15-20 days in shade\n6. Dilute with water 1:5 ratio\n7. Apply directly to soil around plant roots',
         'Use fresh cow dung for best microbial activity.\nKeep the mixture moist but not waterlogged.\nApply early morning or evening for best absorption.',
         'Kitchen waste, Fresh cow dung, Water, Large container, Stirring stick'),
        (farmers[1], 'Drip Irrigation Setup Guide', 'Irrigation',
         'Discover how to set up an affordable drip irrigation system that saves 60% water while increasing crop yields by up to 40%.',
         '1. Survey your field and draw a layout\n2. Install the main water supply pipe\n3. Connect sub-main pipes along crop rows\n4. Attach drip laterals every 30cm\n5. Install pressure regulator and filter\n6. Set timer for morning irrigation\n7. Test all emitters for equal flow',
         'Check emitters weekly for clogging.\nFlush the system monthly.\nInstall a 120-mesh filter to prevent blockages.',
         'HDPE main pipe, Drip laterals, Emitters, Filter unit, Pressure regulator, Timer'),
        (farmers[2], 'Crop Rotation for Soil Health', 'Sustainable Farming',
         'Traditional crop rotation techniques that maintain soil health, prevent pest buildup, and naturally restore nitrogen levels season after season.',
         '1. Divide your field into 4 equal sections\n2. Map your rotation plan: Legume → Cereal → Root vegetable → Leafy green\n3. Plant nitrogen-fixing legumes in depleted sections\n4. Rotate crops every season without repeating\n5. Document soil condition before and after\n6. Add green manure between rotations',
         'Rotate legumes with cereals for best nitrogen fixation.\nNever plant the same family twice in a row.\nAdd compost between rotations.',
         'Rotation planning chart, Different seed varieties, Soil testing kit, Compost'),
        (farmers[3], 'Organic Seed Saving Techniques', 'Seed Conservation',
         'How to select, harvest, dry, and store quality seeds from your best plants to ensure crop continuity and preserve heirloom varieties.',
         '1. Select your healthiest, most productive plants\n2. Allow fruits/pods to fully mature on the plant\n3. Harvest on a dry sunny day\n4. Spread seeds on cloth in shade to dry\n5. Dry for 1-2 weeks until completely moisture-free\n6. Store in paper envelopes or glass jars\n7. Label with variety name and harvest date',
         'Label seeds immediately — memory fades fast!\nDo not store in plastic bags (moisture traps).\nAdd silica gel packets to jars for long-term storage.',
         'Paper bags, Mesh cloth, Glass jars, Labels, Silica gel packets, Permanent marker'),
        (farmers[4], 'Vermicompost Production Guide', 'Organic Farming',
         'Step-by-step guide to creating nutrient-rich vermicompost using red wiggler earthworms — the black gold that transforms any soil.',
         '1. Build or buy a composting bed (60cm x 45cm x 30cm)\n2. Add 10cm bedding of shredded newspaper or coconut coir\n3. Moisten the bedding until damp but not wet\n4. Add 500g of red wiggler earthworms\n5. Add thin layer of food scraps (no citrus, onion, meat)\n6. Cover with cardboard to maintain darkness\n7. Harvest rich compost after 45-60 days',
         'Keep temperature between 15-25 degrees for best worm activity.\nNever add citrus, garlic, onion, or meat scraps.\nThe compost is ready when it smells earthy like forest soil.',
         'Composting bin, Red wiggler worms, Shredded newspaper, Food scraps, Spray bottle, Trowel'),
        (farmers[5], 'Integrated Pest Management', 'Pest Control',
         'Natural and holistic approaches to manage agricultural pests effectively without relying on harmful chemical pesticides.',
         '1. Monitor crops every 3 days for early pest signs\n2. Identify the exact pest species before acting\n3. Introduce natural predators like ladybugs\n4. Set sticky traps for flying insects\n5. Prepare neem oil spray (5ml per litre of water)\n6. Apply neem spray in evening, cover all leaf surfaces\n7. Remove severely infected plants to prevent spread',
         'Early detection reduces 80% of damage.\nNeem oil loses potency in direct sunlight — spray at dusk.\nRotate pest control methods to prevent resistance.',
         'Neem oil, Castile soap, Water, Sprayer, Sticky traps, Magnifying glass'),
        (farmers[0], 'Soil pH Testing and Correction', 'Soil Management',
         'Understanding and correcting your soil pH is the single most important step to improving crop health and yield on any farm.',
         '1. Collect soil samples from 5 spots in your field\n2. Mix samples and test using pH kit or meter\n3. Ideal pH for most crops is 6.0-7.0\n4. If too acidic (below 6): add agricultural lime\n5. If too alkaline (above 7.5): add sulfur or compost\n6. Mix amendments into top 15cm of soil\n7. Retest after 4 weeks',
         'Test soil before every planting season.\nDifferent crops prefer different pH — research your crop.\nExcessive lime application harms soil microbes.',
         'Soil pH test kit, Agricultural lime, Sulfur powder, Trowel, Sample bags'),
        (farmers[1], 'Mulching Benefits and Methods', 'Soil Management',
         'Practical guide to mulching that reduces water usage by 50%, suppresses weeds, and keeps soil temperature stable for better crop growth.',
         '1. Clear weeds from planting area\n2. Water soil thoroughly\n3. Spread organic mulch 5-8cm thick\n4. Keep mulch 5cm away from plant stem\n5. Replenish mulch every 6-8 weeks\n6. Use different materials based on availability',
         'Never let mulch touch the stem — causes rot.\nStraw mulch is best for vegetable gardens.\nGrass clippings decompose fast and add nitrogen.',
         'Straw, Dried leaves, Grass clippings, Newspaper, Coconut coir, Trowel'),
    ]
    k_posts = []
    for i, pd in enumerate(posts_data):
        post = KnowledgePost(user_id=pd[0].id, title=pd[1], category=pd[2],
                              description=pd[3], steps=pd[4], tips=pd[5],
                              materials=pd[6], views=50 + i * 23,
                              rating=round(3.8 + (i % 5) * 0.12, 1),
                              likes=10 + i * 7)
        db.session.add(post)
        k_posts.append(post)

    # ── Products ──
    products_data = [
        (farmers[0], 'Basmati Rice Organic', 'Grains',
         'Premium quality long-grain basmati rice grown organically in Punjab. No pesticides, no chemicals. Aged 1 year for superior aroma.', 45, 'kg', 500),
        (farmers[1], 'Turmeric Finger Premium', 'Spices',
         'Fresh turmeric fingers from Telangana with 5%+ curcumin content. Sun-dried and naturally processed. Ideal for cooking and medicine.', 120, 'kg', 200),
        (farmers[2], 'Red Chillies Dry', 'Spices',
         'Sun-dried Guntur red chillies with excellent ASTA color value. High pungency, low moisture. Perfect for spice export and cooking.', 200, 'kg', 150),
        (farmers[3], 'Organic Wheat Grain', 'Grains',
         'Hard red winter wheat grown without synthetic inputs. Stone-mill quality. Excellent for chapati, bread, and porridge.', 35, 'kg', 800),
        (farmers[4], 'Toor Dal Organic', 'Pulses',
         'Fresh organic toor dal (pigeon peas) from Gujarat. Bold size, low moisture. Rich in protein and traditionally grown variety.', 110, 'kg', 300),
        (farmers[4], 'Raw Peanuts Premium', 'Grains',
         'High-oil content groundnuts from Gujarat farms. Bold Java variety, freshly harvested. Ideal for oil extraction and snacking.', 90, 'kg', 400),
        (farmers[5], 'Black Pepper Organic', 'Spices',
         'Premium black pepper from Kerala Western Ghats spice gardens. Strong piperine content. Hand-picked and sun-dried. Export quality.', 600, 'kg', 100),
        (farmers[5], 'Yellow Mustard Seeds', 'Spices',
         'High-quality yellow mustard seeds from Rajasthan. Low moisture, bold size. Excellent for oil pressing, tempering, and pickling.', 70, 'kg', 250),
        (farmers[2], 'Coriander Seeds', 'Spices',
         'Aromatic coriander seeds from Andhra Pradesh. Split and whole varieties available. Essential spice for every kitchen.', 80, 'kg', 180),
        (farmers[3], 'Chickpea Kabuli', 'Pulses',
         'Large-seeded Kabuli chickpeas from Maharashtra. Low moisture, clean and sortex graded. Perfect for hummus, curries, and export.', 95, 'kg', 350),
        (farmers[0], 'Basmati Broken Rice', 'Grains',
         'Organic broken basmati rice at an affordable price. Perfect for khichdi, porridge, and pet food. Same farm as premium basmati.', 25, 'kg', 600),
        (farmers[1], 'Dried Ginger Slices', 'Spices',
         'Sun-dried ginger slices with high gingerol content. Sourced from organic farms in Telangana. Ideal for teas and Ayurvedic use.', 180, 'kg', 120),
    ]
    prods = []
    for pd in products_data:
        p = Product(seller_id=pd[0].id, name=pd[1], category=pd[2],
                    description=pd[3], price=pd[4], unit=pd[5], stock=pd[6])
        db.session.add(p)
        prods.append(p)

    db.session.flush()

    # ── Orders ──
    orders_data = [
        (prods[0],  buyers[0], farmers[0], 50,  2250,  'completed'),
        (prods[1],  buyers[0], farmers[1], 3,   360,   'shipped'),
        (prods[2],  buyers[1], farmers[2], 2,   400,   'delivered'),
        (prods[3],  buyers[1], farmers[3], 100, 3500,  'completed'),
        (prods[6],  buyers[2], farmers[5], 5,   3000,  'placed'),
        (prods[7],  buyers[2], farmers[5], 10,  700,   'pending'),
        (prods[4],  buyers[3], farmers[4], 20,  2200,  'shipped'),
        (prods[9],  buyers[3], farmers[3], 15,  1425,  'pending'),
        (prods[0],  buyers[2], farmers[0], 10,  450,   'delivered'),
        (prods[10], buyers[0], farmers[0], 25,  625,   'completed'),
    ]
    for od in orders_data:
        o = Order(product_id=od[0].id, buyer_id=od[1].id, seller_id=od[2].id,
                  quantity=od[3], total_amount=od[4], status=od[5])
        db.session.add(o)

    db.session.flush()

    # ── Conversations & Messages ──
    conv_pairs = [
        (buyers[0], farmers[0]),
        (buyers[0], farmers[1]),
        (buyers[1], farmers[2]),
        (buyers[2], farmers[5]),
        (buyers[3], farmers[4]),
        (farmers[0], farmers[1]),
    ]
    conversations = []
    for u1, u2 in conv_pairs:
        conv = Conversation(user1_id=u1.id, user2_id=u2.id)
        db.session.add(conv)
        conversations.append(conv)
    db.session.flush()

    sample_messages = [
        # Hans <-> Ramesh
        [(buyers[0], 'Hi Ramesh, I am interested in your Basmati Rice. Is it still available?'),
         (farmers[0], 'Hello Hans! Yes, it is available. We have 500 kg in stock. Pure organic, aged one year.'),
         (buyers[0], 'Perfect! Can you ship 50 kg to Germany? What are your export rates?'),
         (farmers[0], 'Yes, we can arrange shipping. The price is Rs 45/kg. I will share the export documentation.'),
         (buyers[0], 'Great! Please send me a quality certificate and I will confirm the order today.')],
        # Hans <-> Sita
        [(buyers[0], 'Hi Sita, I need turmeric with high curcumin content. Can you provide lab reports?'),
         (farmers[1], 'Hello Hans! Yes, our turmeric has 5.2% curcumin. I can share the certificate.')],
        # John <-> Arjun
        [(buyers[1], 'Hi Arjun, do you have chillies with ASTA color value above 120?'),
         (farmers[2], 'Yes! Our Guntur chillies have ASTA 130+. We export to the US regularly.'),
         (buyers[1], 'Excellent. Send me 2 kg sample first.')],
        # Sophie <-> Priya
        [(buyers[2], 'Bonjour Priya! I need Kerala black pepper for my Paris restaurant.'),
         (farmers[5], 'Bonjour Sophie! We have Malabar black pepper, freshly harvested this season.'),
         (buyers[2], 'Parfait! Can I get 5 kg to test quality first?'),
         (farmers[5], 'Of course! I will ship samples within 3 days.')],
        # Ahmed <-> Suresh
        [(buyers[3], 'Assalamu Alaikum Suresh, I need toor dal for Dubai export. Minimum 500 kg.'),
         (farmers[4], 'Wa Alaikum Salam Ahmed! We can supply 500 kg with full FSSAI certification.'),
         (buyers[3], 'Please share your latest price list and availability.')],
        # Ramesh <-> Sita (farmer to farmer)
        [(farmers[0], 'Hi Sita! I loved your post on seed saving. Can we collaborate on our next harvest?'),
         (farmers[1], 'That sounds great Ramesh! I have some heirloom rice seeds you might be interested in.'),
         (farmers[0], 'Perfect! Let us connect offline too.')],
    ]
    for i, conv in enumerate(conversations):
        for sender, content in sample_messages[i]:
            db.session.add(Message(conversation_id=conv.id, sender_id=sender.id, content=content))

    # ── Notifications ──
    notifs_data = [
        (farmers[0], 'Your knowledge on "Natural Fertilizer" was liked by 5 farmers.', 'like', '2h ago'),
        (farmers[0], 'New order received for Basmati Rice from Hans Muller (Germany).', 'order', '3h ago'),
        (farmers[0], 'You connected with a buyer from Germany.', 'connect', '1d ago'),
        (farmers[0], 'Your knowledge on "Soil pH Testing" was shared 10 times.', 'share', '2d ago'),
        (farmers[1], 'New order received for Turmeric Finger from Hans Muller.', 'order', '1h ago'),
        (farmers[1], 'Sophie Dubois viewed your profile.', 'connect', '5h ago'),
        (farmers[2], 'Your Chilli product has been viewed 45 times today.', 'share', '1h ago'),
        (farmers[5], 'New order received for Black Pepper from Sophie Dubois.', 'order', '30m ago'),
        (buyers[0],  'Your order for Basmati Rice has been marked as Completed.', 'order', '1d ago'),
        (buyers[0],  'Sita Devi replied to your message.', 'connect', '2h ago'),
    ]
    for nd in notifs_data:
        db.session.add(Notification(user_id=nd[0].id, message=nd[1],
                                    type=nd[2], time_ago=nd[3]))

    # ── Contact Messages (sample) ──
    contact_samples = [
        ('Mukesh Sharma', 'mukesh@farmer.in', 'Farmer Onboarding',
         'I am a farmer from Rajasthan with 20 years of experience in mustard farming. How do I register and list my products on this platform?'),
        ('Emily Watson',  'emily@organics.uk', 'Partnership',
         'We are a UK-based organic food retailer looking to source directly from Indian farmers. Can we discuss a partnership arrangement?'),
        ('Ravi Kumar',    'ravi@agri.co', 'Technical Support',
         'I uploaded my product photo but it is not showing on the marketplace. Please help me fix this issue.'),
    ]
    for cs in contact_samples:
        db.session.add(ContactMessage(name=cs[0], email=cs[1], subject=cs[2], message=cs[3]))

    db.session.commit()
    print('Database seeded successfully!')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, port=5000)
