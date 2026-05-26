import requests
import urllib3
import json
import random
import datetime
import time
from urllib.parse import quote
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from config import PANEL_BASE_URL, PANEL_DOMAIN, PANEL_PORT, PANEL_PATH
# import secret
BASE_URL = "https://panel.ezh-dev.ru:17211/fJRVDuTcoinPdJ4Dnd/"

# admn_username = secret.user
# admn_pass = secret.password
user = "admin"
password = "panel_ezh_admin"
def login():

    admin_login = {
        "username": user,
        "password": password,
    }

    # Список всех возможных путей логина для 3x-ui
    login_paths = [
        "/panel/api/login",
        "/api/login", 
        "/login",
        "/panel/login",
        "/user/login",
        "/admin/login",
    ]
    
    print(f"[INFO] Пробуем логин на {BASE_URL}")
    print(f"[INFO] User: {user}")
    print(f"\n" + "="*80)
    
    for path in login_paths:
        url = f"{BASE_URL}{path}"
        print(f"\n[ПОПЫТКА] POST {url}")
        try:
            response = requests.post(url, json=admin_login, verify=False, timeout=5)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Length: {len(response.text)}")
            print(f"  Body: {response.text[:200]}")
            
            if response.status_code == 200 and response.text:
                try:
                    result = response.json()
                    print(f"  ✓ JSON распарсен успешно!")
                    print(f"  Результат: {result}")
                    if result.get('success'):
                        print(f"\n✓✓✓ ЛОГИН УСПЕШЕН на {path}")
                        return result
                except:
                    print(f"  Ошибка парсинга JSON")
        except Exception as e:
            print(f"  Exception: {e}")
    
    print(f"\n{'='*80}")
    print("✗ Ни один путь не сработал!")
    return {"error": "All login paths failed"}

print(login())