# 🌱 Roots to Reach

**Digitally Empowering Traditional Farming**

A full-stack production-ready web application built with Flask, SQLite, and Vanilla JS.

---

## 🚀 Quick Start

```bash
# 1. Navigate to project folder
cd "Roots to Reach"

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (auto-seeds database)
python app.py
```

Open: **http://localhost:5000**

---

## 🔑 Demo Accounts

| Role   | Email                      | Password   |
|--------|----------------------------|------------|
| Farmer | ramesh@example.com         | farmer123  |
| Buyer  | hans@example.com           | buyer123   |
| Admin  | admin@rootstoreach.com     | admin123   |

---

## 📁 Project Structure

```
Roots to Reach/
├── app.py              # Main Flask application + routes
├── models.py           # SQLAlchemy database models
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── uploads/            # User uploaded images
├── static/
│   ├── css/
│   │   ├── global.css      # Global styles & utilities
│   │   ├── navbar.css      # Navbar & footer
│   │   ├── home.css        # Home page styles
│   │   ├── dashboard.css   # Dashboard & sidebar
│   │   └── pages.css       # All other page styles
│   └── js/
│       └── main.js         # Vanilla JavaScript
└── templates/
    ├── base.html           # Base layout
    ├── home.html           # Landing page
    ├── signup.html         # Registration
    ├── login.html          # Login
    ├── dashboard.html      # User dashboard
    ├── knowledge_hub.html  # Browse knowledge
    ├── knowledge_detail.html
    ├── share_knowledge.html
    ├── my_knowledge.html
    ├── marketplace.html
    ├── product_detail.html
    ├── add_product.html
    ├── orders.html
    ├── messages.html
    ├── profile.html
    ├── settings.html
    ├── about.html
    ├── contact.html
    ├── _sidebar.html       # Shared sidebar component
    ├── admin/
    │   ├── dashboard.html
    │   └── users.html
    └── errors/
        ├── 404.html
        └── 403.html
```

---

## 🎨 Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Python Flask
- **Database:** SQLite + SQLAlchemy ORM
- **Auth:** Flask Session + Werkzeug password hashing
- **Templating:** Jinja2

---

## 📦 Features

- ✅ User registration & login (farmer / buyer / admin)
- ✅ Knowledge Hub — share & browse farming techniques
- ✅ Marketplace — list & buy agricultural products
- ✅ Order management with status tracking
- ✅ Messaging system
- ✅ User profiles
- ✅ Admin panel
- ✅ Fully responsive (mobile-first)
- ✅ Seed data pre-loaded

---

© 2026 Roots to Reach. All rights reserved.
