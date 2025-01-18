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
    "tokenomics": 2,
    "roadmap": 2,
}

thread_keyword_scores = {
    "lfg": 1,
    "go": 1,
    "moon": 1,
    "pump": 1,
    "send it": 1,
}

# API-Daten für Telegram
api_id = 26430719
api_hash = "0daaec8b4c96cfc499ace42cbd9c7939"
phone_number = "+4367761720922"

# Telegram-Client initialisieren
client = TelegramClient("session_name", api_id, api_hash)

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
        total_score -= 4

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

async def analyze_threads(page):
    html_content = await page.content()
    soup = BeautifulSoup(html_content, "html.parser")
    
    thread_posts = soup.find_all("div", class_="flex gap-2 items-start")
    
    total_score = 0
    for post in thread_posts:
        text = post.get_text().lower()
        for keyword, points in thread_keyword_scores.items():
            if keyword in text:
                total_score += points
                print(f"Gefunden in Threads: '{keyword}', Punkte: {points}")
    
    return total_score

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

                    title = soup.title.string if soup.title else "Kein Titel gefunden"
                    ticker_match = re.search(r"\((.*?)\)", title)
                    ticker = ticker_match.group(1) if ticker_match else "Kein Ticker gefunden"
                    print(f"Gefundener Ticker: {ticker}")

                    token_website = None
                    telegram_url = None
                    twitter_url = None

                    for link in soup.find_all("a", href=True):
                        if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                            token_website = link["href"]
                        if "telegram" in link.text.lower():
                            telegram_url = link["href"]

                    total_score = 0

                    if token_website:
                        website_score = keyword_analysis(token_website, ticker)
                        print(f"Punkte aus Website-Analyse: {website_score}")
                        total_score += website_score

                    if telegram_url:
                        telegram_score = await analyze_telegram_group_or_channel(telegram_url, ticker)
                        print(f"Punkte aus Telegram-Analyse: {telegram_score}")
                        total_score += telegram_score
                    
                    thread_score = await analyze_threads(page)
                    print(f"Punkte aus Threads-Analyse: {thread_score}")
                    total_score += thread_score

                    print(f"Gesamtpunktzahl: {total_score}")

                    if total_score > 2:
                        print("Token erfüllt die Kriterien, Bot wird gestoppt.")
                        print(urltoken)
                        market_cap_match = re.search(r"market cap:\s*\$([\d,]+)", html_content, re.IGNORECASE)
        
                        if market_cap_match:
                            market_cap_text = market_cap_match.group(1)
                            market_cap_value = int(market_cap_text.replace(",", ""))
            
                            print(f"Gefundene Market Cap: {market_cap_value} USD")
                            if 9000 <= market_cap_value <= 12000:
                                print("Maketcap im gewünschten Bereich")
                            else:
                                print("Market Cap liegt außerhalb des gewünschten Bereichs.")
                        break

                    await browser.close()

            except PlaywrightTimeoutError:
                print(f"Fehler: Timeout beim Laden der Seite {urltoken}. Fahre mit dem nächsten Token fort.")
            except Exception as e:
                print(f"Fehler beim Verarbeiten von {urltoken}: {e}")

        else:
            print("Keine Token-Links gefunden, versuche es erneut...")
        await asyncio.sleep(10)

asyncio.run(fetch_token_website_and_socials())