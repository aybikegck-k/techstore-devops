"""
TechStore - Selenium UI Test Paketi
Çalıştırmak için önce uygulamayı başlatın: python app.py
Sonra: pytest tests/test_ui.py -v

Gereksinimler:
- Google Chrome kurulu olmalı
- chromedriver: pip install webdriver-manager
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = 'http://localhost:5000'


@pytest.fixture(scope='module')
def driver():
    """Headless Chrome sürücüsü."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,900')

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        drv = webdriver.Chrome(service=service, options=options)
    except Exception:
        drv = webdriver.Chrome(options=options)

    drv.implicitly_wait(5)
    yield drv
    drv.quit()


def test_homepage_loads(driver):
    """Ana sayfa yüklenmeli ve başlık doğru olmalı."""
    driver.get(BASE_URL)
    assert 'TechStore' in driver.title

def test_products_visible(driver):
    """Ana sayfada ürünler görünür olmalı."""
    driver.get(BASE_URL)
    cards = driver.find_elements(By.CLASS_NAME, 'product-card')
    assert len(cards) >= 6, f"Beklenen 6+ ürün, bulunan: {len(cards)}"

def test_product_search(driver):
    """Arama kutusu çalışmalı."""
    driver.get(BASE_URL)
    search = driver.find_element(By.ID, 'search-input')
    search.send_keys('samsung')
    time.sleep(0.8)
    results = driver.find_elements(By.CLASS_NAME, 'search-result-item')
    assert len(results) >= 1

def test_category_filter(driver):
    """Kategori filtresi çalışmalı."""
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 5)
    laptop_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Laptop')]"))
    )
    laptop_btn.click()
    time.sleep(0.5)
    visible_cards = [
        c for c in driver.find_elements(By.CLASS_NAME, 'product-card')
        if c.is_displayed()
    ]
    assert 1 <= len(visible_cards) <= 3

def test_add_to_cart_button(driver):
    """Sepete ekle butonu çalışmalı ve badge güncellemeli."""
    driver.get(BASE_URL)
    initial_badge = driver.find_element(By.ID, 'cart-badge').text
    add_btn = driver.find_elements(By.CLASS_NAME, 'add-btn')[0]
    add_btn.click()
    time.sleep(1)
    new_badge = driver.find_element(By.ID, 'cart-badge').text
    assert int(new_badge) > int(initial_badge or '0')

def test_toast_notification(driver):
    """Sepete ekleme toast mesajı göstermeli."""
    driver.get(BASE_URL)
    add_btn = driver.find_elements(By.CLASS_NAME, 'add-btn')[0]
    add_btn.click()
    time.sleep(0.5)
    toast = driver.find_element(By.ID, 'toast')
    assert 'show' in toast.get_attribute('class')

def test_product_detail_navigation(driver):
    """Ürüne tıklamak detay sayfasına gitme."""
    driver.get(BASE_URL)
    cards = driver.find_elements(By.CLASS_NAME, 'product-card')
    cards[0].click()
    time.sleep(0.5)
    assert '/product/' in driver.current_url

def test_product_detail_page(driver):
    """Ürün detay sayfası özellikleri göstermeli."""
    driver.get(f'{BASE_URL}/product/1')
    assert 'Samsung' in driver.page_source
    assert 'sepete' in driver.page_source.lower() or 'Sepet' in driver.page_source

def test_cart_page_loads(driver):
    """Sepet sayfası yüklenmeli."""
    driver.get(f'{BASE_URL}/cart')
    assert driver.find_element(By.TAG_NAME, 'body')

def test_health_endpoint_via_browser(driver):
    """Sağlık endpoint'i JSON döndürmeli."""
    driver.get(f'{BASE_URL}/health')
    assert 'healthy' in driver.page_source
