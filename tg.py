from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelPrivateError
import time

# API-Daten
api_id = 26430719  # Ersetze durch deine API-ID
api_hash = "0daaec8b4c96cfc499ace42cbd9c7939"
phone_number = "+4367761720922"  # Deine Telefonnummer mit Ländervorwahl

# Telegram-Client initialisieren
client = TelegramClient("session_name", api_id, api_hash)

async def get_member_count(client, entity):
    try:
        full_channel_info = await client(GetFullChannelRequest(entity))
        return full_channel_info.full_chat.participants_count
    except ChannelPrivateError:
        print("Zugriff auf Mitgliederanzahl verweigert.")
        return None
    except Exception as e:
        print(f"Fehler beim Abrufen der Mitgliederanzahl: {e}")
        return None

async def analyze_telegram_group_or_channel(entity):
    async with client:
        entity_details = await client.get_entity(entity)
        chat_title = entity_details.title
        chat_type = "Kanal" if entity_details.broadcast else "Gruppe"
        name_contains_token = "Niggabob".lower() in chat_title.lower()
        
        # Mitgliederanzahl abrufen
        member_count = await get_member_count(client, entity)

        # Nachrichten der letzten Stunde abrufen
        history = await client(GetHistoryRequest(
            peer=entity,
            limit=100,
            offset_date=None,
            add_offset=0,
            min_id=0,
            max_id=0,
            offset_id=0,
            hash=0
        ))

        messages_last_hour = sum(1 for message in history.messages if message.date.timestamp() > (time.time() - 3600))
        
        # Punktevergabe
        if chat_type == "Kanal":
            reactions = 10  # Beispielwert für Kanalreaktionen
            score = evaluate_channel(member_count, reactions, name_contains_token)
        else:
            score = evaluate_group(member_count, messages_last_hour, name_contains_token)

        print(f"Punkte für {chat_title}: {score}")

def evaluate_channel(member_count, reactions, name_contains_token):
    score = 0
    if member_count is not None:
        if member_count > 100:
            score += 3
        if member_count > 500:
            score += 2
    else:
        print("Mitgliederanzahl nicht verfügbar.")

    if reactions > 10:
        score += 2

    score += -7 if not name_contains_token else 0

    return score

def evaluate_group(member_count, messages_last_hour, name_contains_token):
    score = 0
    if member_count is not None:
        if member_count > 100:
            score += 3
        if member_count > 500:
            score += 2
    else:
        print("Mitgliederanzahl nicht verfügbar.")

    if messages_last_hour > 20:
        score += 2
    elif messages_last_hour < 5:
        score -= 2

    score += -7 if not name_contains_token else 0

    return score

# Beispielaufruf
entity = "https://t.me/niggabobsol"
client.loop.run_until_complete(analyze_telegram_group_or_channel(entity))