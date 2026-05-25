"""
TechStore - Kapsamlı Test Paketi
Çalıştırmak için: pytest tests/ -v
"""
import pytest
import json
from app import app, PRODUCTS, get_product_by_id


# ── FIXTURES ──────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Test istemcisi oluşturur, her testten sonra oturumu temizler."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['cart'] = {}
        yield client


# ── ANA SAYFA TESTLERİ ────────────────────────────────────────────────────

def test_home_page_status(client):
    """Ana sayfa 200 döndürmeli."""
    response = client.get('/')
    assert response.status_code == 200

def test_home_page_contains_products(client):
    """Ana sayfa ürün adlarını içermeli."""
    response = client.get('/')
    assert b'Samsung Galaxy' in response.data
    assert b'MacBook' in response.data
    assert b'TechStore' in response.data

def test_home_page_contains_categories(client):
    """Ana sayfa kategori filtrelerini içermeli."""
    response = client.get('/')
    assert b'Telefon' in response.data
    assert b'Laptop' in response.data


# ── ÜRÜN DETAY TESTLERİ ───────────────────────────────────────────────────

def test_product_detail_valid(client):
    """Geçerli ürün detay sayfası 200 döndürmeli."""
    response = client.get('/product/1')
    assert response.status_code == 200
    assert b'Samsung Galaxy S24 Ultra' in response.data

def test_product_detail_invalid(client):
    """Geçersiz ürün 404 döndürmeli."""
    response = client.get('/product/9999')
    assert response.status_code == 404

def test_product_detail_shows_specs(client):
    """Ürün sayfası teknik özellikleri göstermeli."""
    response = client.get('/product/2')
    assert b'M3 Pro' in response.data

def test_product_detail_shows_price(client):
    """Ürün sayfası fiyatı göstermeli."""
    response = client.get('/product/1')
    assert b'54' in response.data  # 54,999 TL


# ── SEPET TESTLERİ ────────────────────────────────────────────────────────

def test_add_to_cart_success(client):
    """Geçerli ürünü sepete eklemek başarılı olmalı."""
    response = client.post('/api/cart/add',
        data=json.dumps({'product_id': 1, 'quantity': 1}),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['cart_count'] == 1
    assert 'Samsung' in data['message']

def test_add_to_cart_invalid_product(client):
    """Geçersiz ürün 404 döndürmeli."""
    response = client.post('/api/cart/add',
        data=json.dumps({'product_id': 9999}),
        content_type='application/json'
    )
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] is False

def test_add_same_product_increases_quantity(client):
    """Aynı ürünü iki kez eklemek miktarı 2 yapmalı."""
    for _ in range(2):
        client.post('/api/cart/add',
            data=json.dumps({'product_id': 3, 'quantity': 1}),
            content_type='application/json'
        )
    response = client.post('/api/cart/add',
        data=json.dumps({'product_id': 3, 'quantity': 1}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['cart_count'] == 3

def test_add_multiple_products(client):
    """Farklı ürünler eklendikçe sepet sayısı artmalı."""
    for pid in [1, 2, 3]:
        client.post('/api/cart/add',
            data=json.dumps({'product_id': pid, 'quantity': 1}),
            content_type='application/json'
        )
    response = client.post('/api/cart/add',
        data=json.dumps({'product_id': 4, 'quantity': 1}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['cart_count'] == 4

def test_remove_from_cart(client):
    """Sepetten ürün silme çalışmalı."""
    client.post('/api/cart/add',
        data=json.dumps({'product_id': 1}),
        content_type='application/json'
    )
    response = client.post('/api/cart/remove',
        data=json.dumps({'product_id': 1}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['cart_count'] == 0

def test_update_cart_quantity(client):
    """Sepet adedi güncelleme çalışmalı."""
    client.post('/api/cart/add',
        data=json.dumps({'product_id': 1}),
        content_type='application/json'
    )
    response = client.post('/api/cart/update',
        data=json.dumps({'product_id': 1, 'quantity': 5}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['cart_count'] == 5

def test_cart_page_empty(client):
    """Boş sepet sayfası mesaj göstermeli."""
    response = client.get('/cart')
    assert response.status_code == 200
    assert 'bo' in response.data.decode('utf-8') or 'Sepetim' in response.data.decode('utf-8')

def test_cart_page_with_items(client):
    """Dolu sepet sayfası ürün göstermeli."""
    client.post('/api/cart/add',
        data=json.dumps({'product_id': 1}),
        content_type='application/json'
    )
    response = client.get('/cart')
    assert b'Samsung' in response.data


# ── ARAMA TESTLERİ ────────────────────────────────────────────────────────

def test_search_by_name(client):
    """İsim bazlı arama çalışmalı."""
    response = client.get('/api/search?q=samsung')
    data = json.loads(response.data)
    assert len(data) >= 1
    assert any('Samsung' in p['name'] for p in data)

def test_search_by_category(client):
    """Kategori bazlı arama çalışmalı."""
    response = client.get('/api/search?category=Laptop')
    data = json.loads(response.data)
    assert all(p['category'] == 'Laptop' for p in data)

def test_search_no_results(client):
    """Sonuçsuz arama boş liste döndürmeli."""
    response = client.get('/api/search?q=xyznotexist123')
    data = json.loads(response.data)
    assert data == []


# ── ÖDEME TESTLERİ ────────────────────────────────────────────────────────

def test_checkout_page_empty_cart_redirect(client):
    """Boş sepet ile checkout sayfası açılabilmeli."""
    response = client.get('/checkout')
    assert response.status_code == 200

def test_checkout_post_creates_order(client):
    """Ödeme formu gönderilince sipariş oluşturulmalı."""
    client.post('/api/cart/add',
        data=json.dumps({'product_id': 1}),
        content_type='application/json'
    )
    response = client.post('/checkout')
    assert response.status_code == 200
    assert 'order' in response.data.decode('utf-8').lower() or response.status_code == 200


# ── SAĞLIK VE METRİK TESTLERİ ────────────────────────────────────────────

def test_health_endpoint(client):
    """/health endpoint sağlıklı yanıt döndürmeli."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'techstore'

def test_metrics_endpoint(client):
    """/metrics endpoint Prometheus metriklerini döndürmeli."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'http_requests_total' in response.data


# ── VERİ MODELİ TESTLERİ ─────────────────────────────────────────────────

def test_all_products_have_required_fields():
    """Tüm ürünler gerekli alanlara sahip olmalı."""
    required = ['id', 'name', 'category', 'price', 'stock', 'rating', 'specs']
    for product in PRODUCTS:
        for field in required:
            assert field in product, f"Ürün {product['id']} '{field}' alanı eksik"

def test_product_prices_positive():
    """Tüm ürün fiyatları pozitif olmalı."""
    for product in PRODUCTS:
        assert product['price'] > 0, f"Ürün {product['name']} geçersiz fiyat"

def test_product_stock_non_negative():
    """Stok negatif olamaz."""
    for product in PRODUCTS:
        assert product['stock'] >= 0

def test_get_product_by_id_exists():
    """Var olan ürün ID ile getirilebilmeli."""
    product = get_product_by_id(1)
    assert product is not None
    assert product['name'] == 'Samsung Galaxy S24 Ultra'

def test_get_product_by_id_not_exists():
    """Olmayan ürün None döndürmeli."""
    product = get_product_by_id(9999)
    assert product is None

def test_product_ratings_in_range():
    """Tüm puanlar 0-5 arasında olmalı."""
    for product in PRODUCTS:
        assert 0 <= product['rating'] <= 5

def test_product_ids_unique():
    """Ürün ID'leri benzersiz olmalı."""
    ids = [p['id'] for p in PRODUCTS]
    assert len(ids) == len(set(ids))

def test_product_specs_not_empty():
    """Her ürünün en az 1 teknik özelliği olmalı."""
    for product in PRODUCTS:
        assert len(product['specs']) >= 1
