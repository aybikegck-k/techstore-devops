from flask import Flask, render_template, request, jsonify, session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid

app = Flask(__name__)
app.secret_key = 'techstore-secret-key-2024'

# ── Prometheus Metrikleri ──────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Toplam HTTP istek sayısı',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP istek süresi',
    ['endpoint']
)
CART_ADD_COUNT = Counter(
    'cart_add_total',
    'Sepete ekleme sayısı',
    ['product_id']
)
ORDER_COUNT = Counter(
    'orders_total',
    'Toplam sipariş sayısı'
)

# ── Gerçekçi Ürün Kataloğu ─────────────────────────────────────────────────
PRODUCTS = [
    {
        'id': 1,
        'name': 'Samsung Galaxy S24 Ultra',
        'category': 'Telefon',
        'price': 54999,
        'stock': 15,
        'rating': 4.8,
        'reviews': 342,
        'image_placeholder': '📱',
        'description': '200MP kamera, S-Pen, Snapdragon 8 Gen 3, 5000mAh batarya',
        'specs': ['200MP Ana Kamera', '12GB RAM', '256GB Depolama', '6.8" QHD+ Ekran'],
        'badge': 'Çok Satan'
    },
    {
        'id': 2,
        'name': 'Apple MacBook Pro 16" M3 Pro',
        'category': 'Laptop',
        'price': 89999,
        'stock': 8,
        'rating': 4.9,
        'reviews': 218,
        'image_placeholder': '💻',
        'description': 'M3 Pro çip, 18GB Unified Memory, 512GB SSD, ProMotion ekran',
        'specs': ['M3 Pro Çip', '18GB Bellek', '512GB SSD', '16.2" Liquid Retina XDR'],
        'badge': 'Editörün Seçimi'
    },
    {
        'id': 3,
        'name': 'Sony WH-1000XM5',
        'category': 'Kulaklık',
        'price': 12499,
        'stock': 25,
        'rating': 4.7,
        'reviews': 891,
        'image_placeholder': '🎧',
        'description': 'Endüstri lideri ANC, 30 saat pil ömrü, LDAC desteği',
        'specs': ['30 Saat Pil', 'LDAC Hi-Res', 'Çoklu Cihaz', 'Hızlı Şarj'],
        'badge': 'En Çok Beğenilen'
    },
    {
        'id': 4,
        'name': 'LG OLED C3 55"',
        'category': 'Televizyon',
        'price': 39999,
        'stock': 6,
        'rating': 4.9,
        'reviews': 156,
        'image_placeholder': '📺',
        'description': '4K OLED evo panel, α9 AI İşlemci, Dolby Vision IQ, webOS 23',
        'specs': ['4K OLED evo', 'α9 Gen6 AI', '120Hz + VRR', 'Dolby Atmos'],
        'badge': 'Sınırlı Stok'
    },
    {
        'id': 5,
        'name': 'iPad Pro 12.9" M2',
        'category': 'Tablet',
        'price': 34999,
        'stock': 12,
        'rating': 4.8,
        'reviews': 423,
        'image_placeholder': '📟',
        'description': 'M2 çip, Liquid Retina XDR, Thunderbolt 4, 5G destekli',
        'specs': ['M2 Çip', '8GB RAM', '256GB WiFi+5G', 'Thunderbolt 4'],
        'badge': None
    },
    {
        'id': 6,
        'name': 'Logitech MX Master 3S',
        'category': 'Aksesuar',
        'price': 2499,
        'stock': 40,
        'rating': 4.7,
        'reviews': 1243,
        'image_placeholder': '🖱️',
        'description': '8000 DPI sensör, MagSpeed manyetik kaydırma, sessiz tıklama',
        'specs': ['8000 DPI', 'MagSpeed Scroll', '70 Gün Pil', 'USB-C Şarj'],
        'badge': 'Fiyat/Performans'
    },
    {
        'id': 7,
        'name': 'DJI Mini 4 Pro',
        'category': 'Drone',
        'price': 28999,
        'stock': 5,
        'rating': 4.8,
        'reviews': 87,
        'image_placeholder': '🚁',
        'description': '4K/60fps video, 45 dk uçuş süresi, Omni yönlü sensörler',
        'specs': ['4K/60fps HDR', '45 Dk Uçuş', 'Omni Obstacle', '20km Video'],
        'badge': 'Yeni'
    },
    {
        'id': 8,
        'name': 'Corsair K100 RGB',
        'category': 'Aksesuar',
        'price': 4299,
        'stock': 18,
        'rating': 4.6,
        'reviews': 534,
        'image_placeholder': '⌨️',
        'description': 'OPX optik-mekanik switch, iCUE AXON teknolojisi, 44-bölgeli RGB',
        'specs': ['OPX Optical', '4000Hz Polling', 'PBT Keycaps', 'Alüminyum Gövde'],
        'badge': None
    }
]

# ── Yardımcı Fonksiyonlar ──────────────────────────────────────────────────
def get_product_by_id(product_id):
    return next((p for p in PRODUCTS if p['id'] == product_id), None)

def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']

def cart_summary(cart):
    total = 0
    count = 0
    for pid, item in cart.items():
        total += item['price'] * item['quantity']
        count += item['quantity']
    return {'total': total, 'count': count}

# ── Middleware: Metrik Kayıt ───────────────────────────────────────────────
@app.before_request
def before_request():
    request._start_time = time.time()

@app.after_request
def after_request(response):
    latency = time.time() - request._start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.endpoint or 'unknown').observe(latency)
    return response

# ── Rotalar ────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    cart = get_cart()
    summary = cart_summary(cart)
    categories = list(set(p['category'] for p in PRODUCTS))
    return render_template('index.html',
                           products=PRODUCTS,
                           categories=categories,
                           cart_count=summary['count'])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return render_template('404.html'), 404
    cart = get_cart()
    summary = cart_summary(cart)
    related = [p for p in PRODUCTS if p['category'] == product['category'] and p['id'] != product_id][:3]
    return render_template('product.html',
                           product=product,
                           related=related,
                           cart_count=summary['count'])

@app.route('/cart')
def cart_page():
    cart = get_cart()
    cart_items = []
    for pid, item in cart.items():
        cart_items.append(item)
    summary = cart_summary(cart)
    return render_template('cart.html',
                           cart_items=cart_items,
                           total=summary['total'],
                           cart_count=summary['count'])

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Ürün bulunamadı'}), 404

    if product['stock'] < quantity:
        return jsonify({'success': False, 'message': 'Yetersiz stok'}), 400

    cart = get_cart()
    pid_str = str(product_id)

    if pid_str in cart:
        cart[pid_str]['quantity'] += quantity
    else:
        cart[pid_str] = {
            'product_id': product_id,
            'name': product['name'],
            'price': product['price'],
            'category': product['category'],
            'emoji': product['image_placeholder'],
            'quantity': quantity
        }

    session['cart'] = cart
    summary = cart_summary(cart)

    CART_ADD_COUNT.labels(product_id=str(product_id)).inc()

    return jsonify({
        'success': True,
        'message': f"{product['name']} sepete eklendi!",
        'cart_count': summary['count'],
        'cart_total': summary['total']
    })

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    cart = get_cart()
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
    summary = cart_summary(cart)
    return jsonify({'success': True, 'cart_count': summary['count'], 'cart_total': summary['total']})

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = data.get('quantity', 1)
    cart = get_cart()
    if product_id in cart:
        if quantity <= 0:
            del cart[product_id]
        else:
            cart[product_id]['quantity'] = quantity
        session['cart'] = cart
    summary = cart_summary(cart)
    return jsonify({'success': True, 'cart_count': summary['count'], 'cart_total': summary['total']})

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '')
    results = PRODUCTS
    if query:
        results = [p for p in results if query in p['name'].lower() or query in p['category'].lower()]
    if category:
        results = [p for p in results if p['category'] == category]
    return jsonify(results)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = get_cart()
    if not cart:
        return render_template('cart.html', cart_items=[], total=0, cart_count=0)
    if request.method == 'POST':
        order_id = str(uuid.uuid4())[:8].upper()
        session['cart'] = {}
        ORDER_COUNT.inc()
        return render_template('order_success.html', order_id=order_id)
    summary = cart_summary(cart)
    cart_items = list(cart.values())
    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=summary['total'],
                           cart_count=summary['count'])

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'techstore', 'version': '1.0.0'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
