#!/usr/bin/env python3
"""
Простой тест логина для отладки
"""
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Параметры
PANEL_DOMAIN = "panel.ezh-dev.ru"
PANEL_PORT = 17211
PANEL_PATH = "fJRVDuTcoinPdJ4Dnd"
USER = "admin"
PASSWORD = "panel_ezh_admin"

# Варианты URL для логина
login_urls = [
    f"https://{PANEL_DOMAIN}:{PANEL_PORT}/{PANEL_PATH}/login",
    f"https://{PANEL_DOMAIN}:{PANEL_PORT}/login",
    f"https://{PANEL_DOMAIN}/{PANEL_PATH}/login",
]

login_data = {
    "username": USER,
    "password": PASSWORD
}

print("="*80)
print("ТЕСТИРОВАНИЕ ЛОГИНА К 3X-UI ПАНЕЛИ")
print("="*80)
print(f"User: {USER}")
print(f"Password: {PASSWORD}")
print(f"Domain: {PANEL_DOMAIN}")
print(f"Port: {PANEL_PORT}")
print(f"Path: {PANEL_PATH}")
print("="*80)

session = requests.Session()
session.verify = False

for login_url in login_urls:
    print(f"\n{'='*80}")
    print(f"ПОПЫТКА: {login_url}")
    print('='*80)
    
    try:
        response = session.post(
            login_url,
            json=login_data,
            verify=False,
            timeout=10,
            allow_redirects=True
        )
        
        print(f"HTTP Статус: {response.status_code}")
        print(f"\nHeaders ответа:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nCookies сессии:")
        for key, value in session.cookies.items():
            print(f"  {key}={value}")
        
        print(f"\nТело ответа (raw):")
        print(f"  Длина: {len(response.text)} символов")
        print(f"  Первые 1000 символов:")
        print("  " + response.text[:1000])
        
        if len(response.text) > 1000:
            print(f"  ... (еще {len(response.text) - 1000} символов)")
        
        print(f"\nПопытка распарсить как JSON:")
        try:
            json_data = response.json()
            print(f"  ✓ Успешно распарсено!")
            print(f"  {json.dumps(json_data, indent=2)}")
        except Exception as e:
            print(f"  ✗ Ошибка парсинга JSON: {e}")
        
        if response.status_code == 200:
            print(f"\n✓✓✓ СТАТУС 200 - Это выглядит как успешный ответ ✓✓✓")
        
    except Exception as e:
        print(f"✗ Exception: {type(e).__name__}: {e}")

print(f"\n{'='*80}")
print("ГОТОВО")
print('='*80)
