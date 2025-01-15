import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import requests
import re
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelPrivateError
import time

# Punktwerte für die Keywords
keyword_scores = {
    "tokenomics": 1,
    "roadmap": 2,
}

# API-Daten für Telegram
api_id = 26430719
api_hash = "0daaec8b4c96cfc499ace42cbd9c7939"
phone_number = "+4367761720922"

# Telegram-Client initialisieren
client = TelegramClient("session_name", api_id, api_hash)

async def fetch_tokens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://pump.fun/advanced"
        await page.goto(url)
        await page.wait_for_selector("tbody[data-testid='virtuoso-item-list']")

        token_links = []
        elements = await page.query_selector_all("tbody[data-testid='virtuoso-item-list'] a")
        for element in elements:
            href = await element.get_attribute("href")
            if href and "/coin/" in href:
                token_links.append(f"https://pump.fun{href}")

        await browser.close()
        return token_links

async def fetch_token_website_and_socials():
    while True:
        token_links = await fetch_tokens()
        if token_links:
            urltoken = token_links[0]
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(urltoken)
                    await page.wait_for_timeout(5000)

                    html_content = await page.content()
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Extrahieren des Tickers
                    title = soup.title.string if soup.title else "Kein Titel gefunden"
                    ticker_match = re.search(r"\((.*?)\)", title)
                    ticker = ticker_match.group(1) if ticker_match else "Kein Ticker gefunden"
                    print(f"Gefundener Ticker: {ticker}")

                    # Token-Website, Telegram und Twitter-URL extrahieren
                    token_website = None
                    telegram_url = None
                    twitter_url = None

                    for link in soup.find_all("a", href=True):
                        if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                            token_website = link["href"]
                        if "telegram" in link.text.lower():
                            telegram_url = link["href"]

                    # Twitter-URL aus Scripts extrahieren
                    script_elements = await page.query_selector_all("script")
                    for element in script_elements:
                        content = await element.inner_text()
                        if "twitter" in content:
                            twitter_match = re.search(r'https://x\.com/[^\"]+', content)
                            if twitter_match:
                                twitter_url = twitter_match.group(0)
                                break

                    await browser.close()

                    total_score = 0

                    if token_website:
                        print(f"Gefundene Token-Website: {token_website}")
                        print(f"Pump-Link: {urltoken}")
                        if twitter_url:
                            print(f"Gefundene Twitter-URL: {twitter_url}")

                        # Punkte aus Keyword-Analyse
                        website_score = keyword_analysis(token_website, ticker)
                        print(f"Punkte aus Website-Analyse: {website_score}")
                        total_score += website_score

                    if telegram_url:
                        print(f"Gefundene Telegram-URL: {telegram_url}")
                        telegram_score = await analyze_telegram_group_or_channel(telegram_url, ticker)
                        print(f"Punkte aus Telegram-Analyse: {telegram_score}")
                        total_score += telegram_score

                    print(f"Gesamtpunktzahl: {total_score}")

                    if total_score > 2:
                        print("Token erfüllt die Kriterien, Bot wird gestoppt.")
                        break

            except PlaywrightTimeoutError:
                print(f"Fehler: Timeout beim Laden der Seite {urltoken}. Fahre mit dem nächsten Token fort.")
            except Exception as e:
                print(f"Fehler beim Verarbeiten von {urltoken}: {e}")

        else:
            print("Keine Token-Links gefunden, versuche es erneut...")
        await asyncio.sleep(10)

def keyword_analysis(url, ticker):
    try:
        response = requests.get(url)
        html_content = response.text.lower()
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Website {url}: {e}")
        return 0

    total_score = 0
    for keyword, points in keyword_scores.items():
        if keyword in html_content:
            total_score += points
            print(f"Gefunden: '{keyword}', Punkte: {points}")

    if ticker.lower() not in html_content:
        print(f"Warnung: Ticker '{ticker}' nicht gefunden.")
        total_score -= 3

    return total_score

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

async def analyze_telegram_group_or_channel(entity, ticker):
    entity = entity.strip().strip('"')
    if entity.startswith("https://t.me/"):
        entity = entity.replace("https://t.me/", "")
    
    async with client:
        try:
            entity_details = await client.get_entity(entity)
            chat_title = entity_details.title
            chat_type = "Kanal" if entity_details.broadcast else "Gruppe"
            name_contains_ticker = ticker.lower() in chat_title.lower()

            member_count = await get_member_count(client, entity)

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

            if chat_type == "Kanal":
                reactions = 10  # Beispielwert für Kanalreaktionen
                score = evaluate_channel(member_count, reactions, name_contains_ticker)
            else:
                score = evaluate_group(member_count, messages_last_hour, name_contains_ticker)

            return score

        except ValueError as e:
            print(f"Fehler: {e} - Überprüfe die Telegram-URL.")
            return 0

def evaluate_channel(member_count, reactions, name_contains_ticker):
    score = 0
    if member_count is not None:
        if member_count > 100:
            score += 3
        if member_count > 500:
            score += 2
    if reactions > 10:
        score += 2

    score += -7 if not name_contains_ticker else 0

    return score

def evaluate_group(member_count, messages_last_hour, name_contains_ticker):
    score = 0
    if member_count is not None:
        if member_count > 100:
            score += 3
        if member_count > 500:
            score += 2
    if messages_last_hour > 20:
        score += 2
    elif messages_last_hour < 5:
        score -= 2

    score += -7 if not name_contains_ticker else 0

    return score

# Starte den Token-Scan
asyncio.run(fetch_token_website_and_socials())