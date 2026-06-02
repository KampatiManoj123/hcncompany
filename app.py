from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from functools import wraps
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_dev_key_change_in_production')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Admin credentials from env
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'hcn@admin2024')

# MongoDB Connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'hcn_db')
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[MONGO_DB_NAME]
    print("✅ MongoDB connected")
except Exception as e:
    print(f"⚠️ MongoDB not available: {e}")
    db = None

def get_db():
    return db

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def serialize(obj):
    if isinstance(obj, list):
        return json.loads(dumps(obj))
    return json.loads(dumps(obj))

# ─── AUTH DECORATORS ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── USER ROUTES ─────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        data = request.json or request.form
        db = get_db()
        if db is None:
            return jsonify({'error': 'DB not connected'}), 500
        email = data.get('email', '').lower().strip()
        if db.users.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 400
        user = {
            'name': data.get('name', ''),
            'email': email,
            'phone': data.get('phone', ''),
            'password': generate_password_hash(data.get('password', '')),
            'created_at': datetime.now(),
            'addresses': [],
            'is_active': True
        }
        result = db.users.insert_one(user)
        session['user_id'] = str(result.inserted_id)
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'success': True, 'redirect': '/account'})
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        data = request.json or request.form
        db = get_db()
        if db is None:
            return jsonify({'error': 'DB not connected'}), 500
        email = data.get('email', '').lower().strip()
        user = db.users.find_one({'email': email})
        if not user or not check_password_hash(user['password'], data.get('password', '')):
            return jsonify({'error': 'Invalid email or password'}), 401
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        # log activity
        db.user_activity.insert_one({
            'user_id': str(user['_id']),
            'action': 'login',
            'details': 'User logged in',
            'created_at': datetime.now(),
            'ip': request.remote_addr
        })
        return jsonify({'success': True, 'redirect': '/account'})
    return render_template('login.html')

@app.route('/logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return redirect('/')

@app.route('/account')
@login_required
def user_account():
    return render_template('account.html')

@app.route('/account/orders')
@login_required
def user_orders():
    return render_template('account_orders.html')

@app.route('/account/profile')
@login_required
def user_profile():
    return render_template('account_profile.html')

# ─── USER API ─────────────────────────────────────────────────────────────────

@app.route('/api/user/me')
@login_required
def api_user_me():
    db = get_db()
    if db is None:
        return jsonify({})
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({})
    user.pop('password', None)
    return jsonify(serialize(user))

@app.route('/api/user/orders')
@login_required
def api_user_orders():
    db = get_db()
    if db is None:
        return jsonify([])
    orders = list(db.orders.find({'user_id': session['user_id']}).sort('created_at', -1))
    return jsonify(serialize(orders))

@app.route('/api/user/activity')
@login_required
def api_user_activity():
    db = get_db()
    if db is None:
        return jsonify([])
    activity = list(db.user_activity.find({'user_id': session['user_id']}).sort('created_at', -1).limit(20))
    return jsonify(serialize(activity))


@app.route('/api/user/orders/<order_id>/cancel', methods=['POST'])
@login_required
def user_cancel_order(order_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    reason = data.get('reason', '').strip()
    if not reason:
        return jsonify({'error': 'Reason required'}), 400
    order = db.orders.find_one({'order_id': order_id, 'user_id': session['user_id']})
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] not in ['Pending', 'Processing']:
        return jsonify({'error': 'Order cannot be cancelled at this stage'}), 400
    db.orders.update_one(
        {'order_id': order_id},
        {'$set': {'status': 'Cancel Requested', 'cancel_reason': reason, 'cancel_requested_at': datetime.now(), 'updated_at': datetime.now()}}
    )
    return jsonify({'success': True})

@app.route('/api/user/profile', methods=['PUT'])
@login_required
def api_update_profile():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    update = {}
    if data.get('name'): update['name'] = data['name']
    if data.get('phone'): update['phone'] = data['phone']
    if data.get('address'): update['address'] = data['address']
    db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': update})
    if data.get('name'):
        session['user_name'] = data['name']
    return jsonify({'success': True})

# ─── DISTRIBUTOR ROUTES ───────────────────────────────────────────────────────

@app.route('/become-a-distributor')
def become_distributor():
    return render_template('distributor.html')

@app.route('/api/distributor/apply', methods=['POST'])
def apply_distributor():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    application = {
        'app_id': 'DIST' + str(uuid.uuid4())[:8].upper(),
        'shop_name': data.get('shop_name', ''),
        'owner_name': data.get('owner_name', ''),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'whatsapp': data.get('whatsapp', ''),
        'address': data.get('address', ''),
        'city': data.get('city', ''),
        'state': data.get('state', ''),
        'pincode': data.get('pincode', ''),
        'gst_number': data.get('gst_number', ''),
        'shop_type': data.get('shop_type', ''),
        'monthly_volume': data.get('monthly_volume', ''),
        'experience': data.get('experience', ''),
        'message': data.get('message', ''),
        'status': 'Pending',
        'created_at': datetime.now()
    }
    db.distributor_applications.insert_one(application)
    return jsonify({'success': True, 'app_id': application['app_id']})

# ─── ADMIN AUTH ───────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.json or request.form
        if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_name'] = 'Admin'
            return jsonify({'success': True, 'redirect': '/admin'})
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    return redirect('/admin/login')

# ─── MAIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/products')
def products_page():
    return render_template('products.html')

@app.route('/cart')
def cart_page():
    return render_template('cart.html')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

@app.route('/order-success/<order_id>')
def order_success(order_id):
    return render_template('order_success.html', order_id=order_id)

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/products')
@admin_required
def admin_products():
    return render_template('admin/products.html')

@app.route('/admin/orders')
@admin_required
def admin_orders():
    return render_template('admin/orders.html')

@app.route('/admin/billing')
@admin_required
def admin_billing():
    return render_template('admin/billing.html')

@app.route('/admin/distributors')
@admin_required
def admin_distributors():
    return render_template('admin/distributors.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    return render_template('admin/users.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── API: PRODUCTS ────────────────────────────────────────────────────────────

@app.route('/api/products', methods=['GET'])
def get_products():
    db = get_db()
    if db is None:
        return jsonify([])
    category = request.args.get('category')
    search = request.args.get('search')
    query = {}
    if category and category != 'all':
        query['category'] = category
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    products = list(db.products.find(query))
    return jsonify(serialize(products))

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    if db is None:
        return jsonify({})
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(serialize(product))

@app.route('/api/products', methods=['POST'])
@admin_required
def add_product():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/uploads/{filename}'
    product = {
        'name': request.form.get('name', ''),
        'category': request.form.get('category', ''),
        'price': float(request.form.get('price', 0)),
        'mrp': float(request.form.get('mrp', 0)),
        'stock': int(request.form.get('stock', 0)),
        'description': request.form.get('description', ''),
        'features': request.form.get('features', '').split('\n') if request.form.get('features') else [],
        'weight': request.form.get('weight', ''),
        'sku': request.form.get('sku', ''),
        'image': image_url,
        'is_new': request.form.get('is_new') == 'true',
        'is_bestseller': request.form.get('is_bestseller') == 'true',
        'created_at': datetime.now()
    }
    result = db.products.insert_one(product)
    product['_id'] = str(result.inserted_id)
    return jsonify(product), 201

@app.route('/api/products/<product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    update_data = {}
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            update_data['image'] = f'/uploads/{filename}'
    fields = ['name', 'category', 'description', 'features', 'weight', 'sku']
    for f in fields:
        if request.form.get(f) is not None:
            update_data[f] = request.form.get(f)
    for f in ['price', 'mrp']:
        if request.form.get(f) is not None:
            update_data[f] = float(request.form.get(f))
    if request.form.get('stock') is not None:
        update_data['stock'] = int(request.form.get('stock'))
    update_data['is_new'] = request.form.get('is_new') == 'true'
    update_data['is_bestseller'] = request.form.get('is_bestseller') == 'true'
    db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
    return jsonify({'success': True})

@app.route('/api/products/<product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    db.products.delete_one({'_id': ObjectId(product_id)})
    return jsonify({'success': True})

# ─── API: USER CART (persistent) ─────────────────────────────────────────────

@app.route('/api/user/cart', methods=['GET'])
@login_required
def get_user_cart():
    db = get_db()
    if db is None:
        return jsonify([])
    cart_doc = db.user_carts.find_one({'user_id': session['user_id']})
    if not cart_doc:
        return jsonify([])
    items = cart_doc.get('items', [])
    # Validate each item against current products
    result = []
    for item in items:
        prod = db.products.find_one({'_id': ObjectId(item['_id'])}) if item.get('_id') else None
        if prod:
            item['available'] = True
            item['name'] = prod['name']
            item['price'] = prod['price']
            item['image'] = prod.get('image', '')
            item['stock'] = prod.get('stock', 0)
        else:
            item['available'] = False
        result.append(item)
    return jsonify(serialize(result))

@app.route('/api/user/cart', methods=['POST'])
@login_required
def save_user_cart():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    items = data.get('items', [])
    db.user_carts.update_one(
        {'user_id': session['user_id']},
        {'$set': {'user_id': session['user_id'], 'items': items, 'updated_at': datetime.now()}},
        upsert=True
    )
    return jsonify({'success': True})

@app.route('/api/user/cart/clear', methods=['POST'])
@login_required
def clear_user_cart():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    db.user_carts.update_one(
        {'user_id': session['user_id']},
        {'$set': {'items': [], 'updated_at': datetime.now()}},
        upsert=True
    )
    return jsonify({'success': True})

# ─── API: USER ACTIVITY DELETE ────────────────────────────────────────────────

@app.route('/api/user/activity/clear', methods=['DELETE'])
@login_required
def clear_user_activity():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    db.user_activity.delete_many({'user_id': session['user_id']})
    return jsonify({'success': True})

@app.route('/api/user/activity/<activity_id>', methods=['DELETE'])
@login_required
def delete_user_activity(activity_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    db.user_activity.delete_one({'_id': ObjectId(activity_id), 'user_id': session['user_id']})
    return jsonify({'success': True})

@app.route('/api/orders', methods=['POST'])
def place_order():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    items = data.get('items', [])
    total = sum(item['price'] * item['qty'] for item in items)
    if total < 999:
        return jsonify({'error': 'Minimum order value is ₹999', 'total': total}), 400
    order = {
        'order_id': 'HCN' + str(uuid.uuid4())[:8].upper(),
        'user_id': session.get('user_id', 'guest'),
        'customer': data.get('customer', {}),
        'items': items,
        'total': total,
        'status': 'Pending',
        'payment_method': data.get('payment_method', 'COD'),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    result = db.orders.insert_one(order)
    order['_id'] = str(result.inserted_id)
    # log activity if user logged in
    if session.get('user_id'):
        db.user_activity.insert_one({
            'user_id': session['user_id'],
            'action': 'order_placed',
            'details': f"Order {order['order_id']} placed for ₹{total:.2f}",
            'created_at': datetime.now()
        })
    return jsonify({'success': True, 'order_id': order['order_id']}), 201

@app.route('/api/orders', methods=['GET'])
@admin_required
def get_orders():
    db = get_db()
    if db is None:
        return jsonify([])
    orders = list(db.orders.find().sort('created_at', -1))
    return jsonify(serialize(orders))

@app.route('/api/orders/<order_id>', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    db.orders.update_one(
        {'order_id': order_id},
        {'$set': {'status': data.get('status'), 'updated_at': datetime.now()}}
    )
    return jsonify({'success': True})


@app.route('/api/orders/<order_id>/delete', methods=['DELETE'])
@admin_required
def delete_order(order_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    order = db.orders.find_one({'order_id': order_id})
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order.get('status') not in ['Delivered', 'Cancelled']:
        return jsonify({'error': 'Only completed or cancelled orders can be deleted'}), 400
    db.orders.delete_one({'order_id': order_id})
    return jsonify({'success': True})

# ─── API: BILLING ─────────────────────────────────────────────────────────────

@app.route('/api/billing', methods=['POST'])
@admin_required
def create_bill():
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    items = data.get('items', [])
    subtotal = sum(item['price'] * item['qty'] for item in items)
    discount = data.get('discount', 0)
    gst_rate = float(data.get('gst_rate', 18)) / 100
    taxable = subtotal - discount
    tax = round(taxable * gst_rate, 2)
    total = round(taxable + tax, 2)
    bill = {
        'bill_id': 'BILL' + str(uuid.uuid4())[:8].upper(),
        'customer': data.get('customer', {}),
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'gst_rate': int(data.get('gst_rate', 18)),
        'total': total,
        'payment_method': data.get('payment_method', 'Cash'),
        'created_at': datetime.now(),
        'created_by': 'Admin'
    }
    result = db.bills.insert_one(bill)
    bill['_id'] = str(result.inserted_id)
    return jsonify(serialize(bill)), 201

@app.route('/api/billing', methods=['GET'])
@admin_required
def get_bills():
    db = get_db()
    if db is None:
        return jsonify([])
    bills = list(db.bills.find().sort('created_at', -1))
    return jsonify(serialize(bills))

@app.route('/api/billing/<bill_id>', methods=['DELETE'])
@admin_required
def delete_bill(bill_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    result = db.bills.delete_one({'bill_id': bill_id})
    if result.deleted_count == 0:
        return jsonify({'error': 'Bill not found'}), 404
    return jsonify({'success': True})

# ─── API: DISTRIBUTORS ────────────────────────────────────────────────────────

@app.route('/api/distributors', methods=['GET'])
@admin_required
def get_distributors():
    db = get_db()
    if db is None:
        return jsonify([])
    apps = list(db.distributor_applications.find().sort('created_at', -1))
    return jsonify(serialize(apps))

@app.route('/api/distributors/<app_id>', methods=['PUT'])
@admin_required
def update_distributor(app_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    data = request.json
    db.distributor_applications.update_one(
        {'app_id': app_id},
        {'$set': {'status': data.get('status'), 'admin_notes': data.get('notes', ''), 'updated_at': datetime.now()}}
    )
    return jsonify({'success': True})

# ─── API: USERS (admin) ───────────────────────────────────────────────────────

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    db = get_db()
    if db is None:
        return jsonify([])
    users = list(db.users.find({}, {'password': 0}).sort('created_at', -1))
    return jsonify(serialize(users))


@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    db = get_db()
    if db is None:
        return jsonify({'error': 'DB not connected'}), 500
    db.users.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'success': True})

# ─── API: STATS ───────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
@admin_required
def get_stats():
    db = get_db()
    if db is None:
        return jsonify({'products': 0, 'orders': 0, 'revenue': 0, 'pending': 0, 'distributors': 0, 'users': 0})
    products = db.products.count_documents({})
    orders = db.orders.count_documents({})
    pending = db.orders.count_documents({'status': 'Pending'})
    pipeline = [{'$group': {'_id': None, 'total': {'$sum': '$total'}}}]
    rev = list(db.orders.aggregate(pipeline))
    revenue = rev[0]['total'] if rev else 0
    distributors = db.distributor_applications.count_documents({'status': 'Pending'})
    users = db.users.count_documents({})
    return jsonify({'products': products, 'orders': orders, 'revenue': revenue, 'pending': pending, 'distributors': distributors, 'users': users})

# ─── CONTEXT PROCESSOR ────────────────────────────────────────────────────────

@app.context_processor
def inject_user():
    return {
        'current_user': {
            'logged_in': 'user_id' in session,
            'name': session.get('user_name', ''),
            'email': session.get('user_email', '')
        },
        'admin_logged_in': session.get('admin_logged_in', False)
    }

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)
