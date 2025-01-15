import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import time

# URL zur Überwachung
URL_TO_MONITOR = "https://pump.fun/advanced"

# Benutzerdefinierter Token-Name zur Überprüfung
target_token_name = input("Bitte geben Sie den zu überwachenden Token-Namen ein: ")

# Funktion zum Extrahieren des neuesten Token-Links
async def fetch_latest_token_link(page):
    await page.goto(URL_TO_MONITOR)
    await page.wait_for_selector("tbody[data-testid='virtuoso-item-list']")

    elements = await page.query_selector_all("tbody[data-testid='virtuoso-item-list'] a")
    for element in elements:
        href = await element.get_attribute("href")
        if href and "/coin/" in href:
            return f"https://pump.fun{href}"
    return None

# Funktion zum Extrahieren des Token-Namens von der Zielseite
async def extract_token_name(page):
    html_content = await page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Extrahieren des Token-Namens aus dem Titel
    title = soup.title.string if soup.title else "Kein Titel gefunden"
    name_match = re.search(r"^(.*?)\(", title)
    token_name = name_match.group(1).strip() if name_match else "Kein Token-Name gefunden"
    return token_name

# Hauptlogik zur Überwachung neuer Token-Links
async def monitor_new_tokens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        last_seen_link = None

        while True:
            try:
                print(f"⚡ Überprüfe auf neue Token-Links unter {URL_TO_MONITOR}")
                latest_link = await fetch_latest_token_link(page)

                if latest_link and latest_link != last_seen_link:
                    print(f"Neuer Token-Link entdeckt: {latest_link}")
                    last_seen_link = latest_link

                    # Gehe zur Token-Seite und extrahiere den Token-Namen
                    await page.goto(latest_link)
                    token_name = await extract_token_name(page)

                    print(f"Gefundener Token-Name: {token_name}")

                    if target_token_name.lower() in token_name.lower():
                        print(f"✔ Ziel-Token '{target_token_name}' im Token-Namen '{token_name}' gefunden!")
                    else:
                        print(f"✖ Ziel-Token '{target_token_name}' nicht im Token-Namen '{token_name}' enthalten.")

                    # Kehre zur Überwachungsseite zurück
                    await page.goto(URL_TO_MONITOR)

                else:
                    print("Kein neuer Link gefunden. Warte...")

            except PlaywrightTimeoutError:
                print("Timeout beim Laden der Seite. Versuche es erneut...")
            except Exception as e:
                print(f"Fehler: {e}")

        await browser.close()

# Starte den Token-Scan
asyncio.run(monitor_new_tokens())