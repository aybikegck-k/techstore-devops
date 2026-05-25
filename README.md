# 🛒 TechStore — Uygulamalı DevOps Projesi

Gerçekçi bir e-ticaret uygulaması üzerinde tam DevOps pipeline'ı.

## Proje Yapısı

```
techstore/
├── app.py                    # Ana Flask uygulaması
├── requirements.txt          # Python bağımlılıkları
├── Dockerfile                # Container tanımı
├── docker-compose.yml        # Tüm servisler (App + Prometheus + Grafana + SonarQube)
├── Jenkinsfile               # CI/CD pipeline
├── sonar-project.properties  # SonarQube yapılandırması
├── templates/
│   ├── index.html            # Ana sayfa (ürün listesi)
│   ├── product.html          # Ürün detay sayfası
│   ├── cart.html             # Sepet sayfası
│   ├── checkout.html         # Ödeme sayfası
│   └── order_success.html    # Sipariş onayı
├── tests/
│   ├── test_app.py           # 25+ birim ve entegrasyon testi
│   └── test_ui.py            # Selenium UI testleri
└── monitoring/
    └── prometheus.yml        # Prometheus scrape yapılandırması
```

## Ürün Kataloğu

| Ürün | Kategori | Fiyat |
|------|----------|-------|
| Samsung Galaxy S24 Ultra | Telefon | 54,999 TL |
| Apple MacBook Pro 16" M3 Pro | Laptop | 89,999 TL |
| Sony WH-1000XM5 | Kulaklık | 12,499 TL |
| LG OLED C3 55" | Televizyon | 39,999 TL |
| iPad Pro 12.9" M2 | Tablet | 34,999 TL |
| Logitech MX Master 3S | Aksesuar | 2,499 TL |
| DJI Mini 4 Pro | Drone | 28,999 TL |
| Corsair K100 RGB | Aksesuar | 4,299 TL |

---

## 🚀 Hızlı Başlangıç

### Ön Gereksinimler

```bash
python3 --version    # 3.9+
docker --version     # 20+
git --version        # 2+
```

### 1. Yerel Çalıştırma

```bash
# Klonla
git clone https://github.com/kullanici-adi/techstore.git
cd techstore

# Sanal ortam kur
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı başlat
python app.py
# → http://localhost:5000
```

### 2. Docker ile Çalıştırma

```bash
# Sadece uygulama
docker build -t techstore-app .
docker run -p 5000:5000 techstore-app

# Tüm stack (Uygulama + Prometheus + Grafana + SonarQube)
docker-compose up -d
```

Servisler:
| Servis | URL | Kimlik |
|--------|-----|--------|
| TechStore | http://localhost:5000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / techstore123 |
| SonarQube | http://localhost:9000 | admin / admin |

---

## 🧪 Testler

### Birim ve Entegrasyon Testleri

```bash
source venv/bin/activate

# Tüm testleri çalıştır
pytest tests/test_app.py -v

# Kapsam raporu ile
pytest tests/test_app.py -v --cov=app --cov-report=term-missing

# Belirli bir test
pytest tests/test_app.py::test_add_to_cart_success -v
```

### UI Testleri (Selenium)

```bash
# Önce uygulamayı başlatın (python app.py)
# ChromeDriver otomatik indirmek için:
pip install webdriver-manager

pytest tests/test_ui.py -v
```

---

## 🔄 CI/CD Pipeline (Jenkins)

### Jenkins Kurulum

```bash
# Docker ile Jenkins
docker run -d \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts

# İlk şifreyi al
docker logs jenkins | grep -A 3 "Please use"
```

### Jenkins Yapılandırması

1. `http://localhost:8080` → Kurulum sihirbazını tamamlayın
2. Plugins: **Pipeline**, **GitHub**, **SonarQube Scanner**, **Slack Notification**, **Docker Pipeline**, **Cobertura**
3. Credentials ekle:
   - `sonar-token` → SonarQube token
   - `docker-hub-creds` → Docker Hub kullanıcı adı/şifre
4. **New Item** → **Pipeline** → SCM: Git (GitHub repo URL)
5. GitHub Webhook: `http://JENKINS_IP:8080/github-webhook/`

### Pipeline Aşamaları

```
Checkout → Setup → Unit Tests → SonarQube → Quality Gate
    → Docker Build → Docker Push → Deploy → Smoke Test → UI Tests
```

---

## 📊 İzleme (Prometheus + Grafana)

### Mevcut Metrikler

| Metrik | Açıklama |
|--------|----------|
| `http_requests_total` | HTTP istek sayacı (method, endpoint, status) |
| `http_request_duration_seconds` | İstek süresi histogramı |
| `cart_add_total` | Sepete ekleme sayacı (product_id) |
| `orders_total` | Tamamlanan sipariş sayacı |

### Grafana Dashboard Sorguları

```promql
# Dakikada istek sayısı
rate(http_requests_total[1m])

# 95. yüzdelik istek süresi
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# En çok eklenen ürünler
topk(5, cart_add_total)

# Hata oranı
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

---

## 📱 API Referansı

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/` | Ana sayfa |
| GET | `/product/<id>` | Ürün detayı |
| GET | `/cart` | Sepet sayfası |
| POST | `/api/cart/add` | Sepete ekle `{"product_id": 1, "quantity": 1}` |
| POST | `/api/cart/remove` | Sepetten sil `{"product_id": 1}` |
| POST | `/api/cart/update` | Miktar güncelle `{"product_id": 1, "quantity": 3}` |
| GET | `/api/search?q=samsung&category=Telefon` | Ürün ara |
| GET | `/checkout` | Ödeme sayfası |
| POST | `/checkout` | Sipariş oluştur |
| GET | `/health` | Sağlık kontrolü |
| GET | `/metrics` | Prometheus metrikleri |

---

## 🎯 Kalite Metrikleri

| Metrik | Hedef |
|--------|-------|
| Test kapsamı | > %80 |
| Test sayısı | 25+ birim, 10+ UI |
| Hata oranı | < %1 |
| Yanıt süresi (p95) | < 500ms |
| Deploy süresi | < 5 dakika |
| SonarQube puanı | A |
