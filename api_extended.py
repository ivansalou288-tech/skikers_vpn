# Extended API functions for VPN client management

from api import (
    add_client,
    get_clients,
    set_subscription_expiry_on_panel,
    find_clients_for_tg_on_inbound,
    parse_inbound_settings,
    panel_session,
    panel_del_client_by_email,
    generate_sub_prefix,
    panel_add_client_to_inbounds,
)
import json
import secrets


def add_client_to_all_inbounds(username: str, tg_id: int, date: str, sub_id: str = None):
    """
    Один общый subId на всех инбаундах: subId = {prefix}_{tg_id}.
    Добавляет клиента на ВСЕ СУЩЕСТВУЮЩИЕ инбаунды основного сервера одним запросом.
    
    :param username: Имя пользователя (префикс для subId)
    :param tg_id: Telegram ID клиента
    :param date: Дата окончания в формате ДД.МММ.ГГГГ
    :param sub_id: (опционально) Готовый sub_id. Если не передан, генерируется новый
    """
    # Если sub_id передан, используем его и извлекаем prefix
    if sub_id:
        universal_sub_id = sub_id
        parts = sub_id.rsplit('_', 1)
        sub_prefix = parts[0] if len(parts) > 1 else sub_id
        print(f"[API] Using provided sub_id: {universal_sub_id} (prefix: {sub_prefix})")
    else:
        # Генерируем новый prefix если sub_id не передан (без буквы 't')
        sub_prefix = username if username and username.strip() else generate_sub_prefix(8)
        universal_sub_id = f"{sub_prefix}_{tg_id}"
        print(f"[API] Generated new sub_id: {universal_sub_id} (prefix: {sub_prefix})")

    # Получаем список существующих инбаундов
    clients_data = get_clients()
    if not clients_data.get("success"):
        return {
            "success": False,
            "message": "Failed to get inbounds list",
            "subId": universal_sub_id,
            "client_prefix": sub_prefix,
            "results": [],
        }
    
    existing_inbound_ids = [inbound.get("id") for inbound in clients_data.get("obj", [])]
    
    if not existing_inbound_ids:
        return {
            "success": False,
            "message": "No inbounds available",
            "subId": universal_sub_id,
            "client_prefix": sub_prefix,
            "results": [],
        }
    
    # Определяем протокол первого инбаунда
    target_inbound = None
    for inbound in clients_data.get("obj", []):
        if inbound.get("id") == existing_inbound_ids[0]:
            target_inbound = inbound
            break
    
    if not target_inbound:
        return {
            "success": False,
            "message": "Failed to determine protocol",
            "subId": universal_sub_id,
            "client_prefix": sub_prefix,
            "results": [],
        }
    
    protocol = target_inbound.get("protocol", "vless")
    
    # Подготавливаем данные клиента
    from api import convert_date_to_timestamp
    expiry_timestamp = convert_date_to_timestamp(date)
    if isinstance(expiry_timestamp, str):
        return {"error": expiry_timestamp}
    
    client_data = {
        "email": f"{sub_prefix}_{tg_id}",
        "limitIp": 0,
        "totalGB": 0,
        "expiryTime": expiry_timestamp,
        "enable": True,
        "tgId": tg_id,
        "subId": universal_sub_id,
        "comment": "",
        "reset": 0,
    }
    
    print(f"[API] Adding client to all inbounds {existing_inbound_ids} with subId={universal_sub_id}")
    print(f"[API] Client data: {json.dumps(client_data, indent=2)}")
    
    # Добавляем клиента одним запросом на все инбаунды
    result = panel_add_client_to_inbounds(client_data, existing_inbound_ids, protocol)
    
    return {
        "success": result.get("success", False),
        "message": result.get("msg", "Client creation completed"),
        "subId": universal_sub_id,
        "client_prefix": sub_prefix,
        "inbound_ids": existing_inbound_ids,
        "details": result,
    }

def renew_subscription_all_inbounds(tg_id: int, additional_months: int):
    """Удаляет старую подписку со всех серверов и создаёт новую с продлённым сроком."""
    from api import renew_subscription
    try:
        return renew_subscription(tg_id, additional_months)
    except Exception as e:
        return {"success": False, "error": str(e)}

def dell_client(inbound_id: int, tg_id: int):
    """Удаляет всех клиентов с данным tgId на указанном inbound (delClientByEmail)."""
    clients_data = get_clients()
    if not clients_data.get("success"):
        return {"error": "Failed to get clients"}

    target_inbound = None
    for inbound in clients_data.get("obj", []):
        if inbound.get("id") == inbound_id:
            target_inbound = inbound
            break
    if not target_inbound:
        return {"error": f"Inbound {inbound_id} not found"}

    settings_obj = parse_inbound_settings(target_inbound)
    if not settings_obj:
        return {"error": "Failed to parse settings"}

    matches = find_clients_for_tg_on_inbound(settings_obj, tg_id, inbound_id)
    if not matches:
        return {"success": True, "message": f"No client tgId={tg_id} on inbound {inbound_id}"}

    session, err = panel_session()
    if session is None:
        return {"error": err or "Login failed"}

    last = None
    for m in matches:
        em = m.get("email")
        if em:
            last = panel_del_client_by_email(session, inbound_id, em)
    return last or {"success": True, "message": f"Client deleted from inbound {inbound_id}"}

def getSubById(telegram_id):
    """Get client info by Telegram ID across all inbounds"""
    clients_data = get_clients()
    
    if not clients_data.get('success'):
        return {"error": "Failed to get clients", "details": clients_data}
    
    inbounds = clients_data.get('obj', [])
    
    for inbound in inbounds:
        if 'settings' in inbound:
            settings = inbound['settings']
            
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except json.JSONDecodeError:
                    continue
            
            if 'clients' in settings:
                clients = settings['clients']
                
                for client in clients:
                    client_tgId = client.get('tgId')
                    if str(client_tgId) == str(telegram_id):
                        return {
                            "success": True,
                            "subId": client.get('subId'),
                            "client_info": {
                                "id": client.get('id'),
                                "email": client.get('email'),
                                "enable": client.get('enable'),
                                "expiryTime": client.get('expiryTime'),
                                "totalGB": client.get('totalGB')
                            },
                            "inbound_id": inbound.get('id')
                        }
    
    return {"error": f"No client found with tgId: {telegram_id}"}

def admin_add_client(tg_id: int, months: int = 1, end_date: str = None):
    """Админ: новый клиент на 4 инбаунда или выставить тот же срок существующему (не суммировать месяцы)."""
    from datetime import datetime
    import time

    try:
        months = int(months) if months is not None else 1

        if end_date:
            try:
                target_date = datetime.strptime(end_date, "%d.%m.%Y")
                new_expiry_ms = int(target_date.timestamp() * 1000)
                calculated_end_date = end_date
            except ValueError:
                return {"success": False, "error": f"Invalid date format: {end_date}. Use DD.MM.YYYY"}
        else:
            current_time_ms = int(time.time() * 1000)
            new_expiry_ms = current_time_ms + months * 30 * 24 * 60 * 60 * 1000
            calculated_end_date = datetime.fromtimestamp(new_expiry_ms / 1000).strftime("%d.%m.%Y")

        print(f"[ADMIN] TG ID: {tg_id}, end_date={calculated_end_date}, months={months}")

        existing_client = getSubById(tg_id)
        if existing_client.get("success"):
            print("[ADMIN] Client exists — выставляем абсолютную дату окончания (без +месяцев к остатку)")
            result = set_subscription_expiry_on_panel(tg_id, new_expiry_ms)
            sub_id = existing_client.get("subId") or ""
            display_user = f"user_{tg_id}"
            action = "updated"
        else:
            print("[ADMIN] Creating new client on all inbounds")
            result = add_client_to_all_inbounds("", tg_id, calculated_end_date)
            sub_id = result.get("subId", "")
            display_user = result.get("client_prefix", "")
            action = "added"

        ok = bool(result.get("success"))

        return {
            "success": ok,
            "message": f"Client {action} successfully" if ok else (result.get("error") or "Operation failed"),
            "tg_id": tg_id,
            "username": display_user,
            "subId": sub_id,
            "months": months,
            "end_date": calculated_end_date,
            "result": result,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
