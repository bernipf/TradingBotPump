import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import time

# Punktwerte für die Keywords
keyword_scores = {
    "tokenomics": 1,
    "roadmap": 2,
}

# URL zur Überwachung
URL_TO_MONITOR = "https://pump.fun/advanced?searchTerm=Nigasaurus"

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

                    # Gehe zur Token-Seite und analysiere kurz
                    await page.goto(latest_link)
                    await page.wait_for_timeout(5000)  # Simulierte Analysezeit

                    # Kehre zur Überwachungsseite zurück
                    await page.goto(URL_TO_MONITOR)

                else:
                    print("Kein neuer Link gefunden. Warte...")

                # Wartezeit zwischen den Überprüfungen
                await asyncio.sleep(10)

            except PlaywrightTimeoutError:
                print("Timeout beim Laden der Seite. Versuche es erneut...")
            except Exception as e:
                print(f"Fehler: {e}")

        await browser.close()

# Starte den Token-Scan
asyncio.run(monitor_new_tokens())