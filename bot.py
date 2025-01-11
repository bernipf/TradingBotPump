import nest_asyncio
nest_asyncio.apply()

import asyncio
from playwright.async_api import async_playwright

async def fetch_tokens():
    async with async_playwright() as p:
        # Browser starten
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Ziel-URL aufrufen
        url = "https://pump.fun/advanced"
        await page.goto(url)

        # Auf dynamische Inhalte warten
        await page.wait_for_selector("tbody[data-testid='virtuoso-item-list']")

        # Links extrahieren
        token_links = []
        elements = await page.query_selector_all("tbody[data-testid='virtuoso-item-list'] a")
        for element in elements:
            href = await element.get_attribute("href")
            if "/coin/" in href:
                token_links.append(f"https://pump.fun{href}")

        # Browser schließen
        await browser.close()

        # Ergebnisse ausgeben
        if token_links:
            print(f"Gefundene Token-Links: {token_links}")
            print(f"Neuester Token-Link: {token_links[0]}")
        else:
            print("Keine Token-Links gefunden.")

# Async-Funktion ausführen
loop = asyncio.get_event_loop()
loop.run_until_complete(fetch_tokens())


from selenium import webdriver

# Browser-Optionen konfigurieren
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Unsichtbarer Modus
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Browser starten
driver = webdriver.Chrome(options=options)

# Pump.fun-Seite laden
url = "https://pump.fun/coin/2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump"
driver.get(url)

# HTML-Inhalt der Seite abrufen
html = driver.page_source

from bs4 import BeautifulSoup

# HTML analysieren
soup = BeautifulSoup(html, "html.parser")

# Token-Links extrahieren
token_links = []
for link in soup.find_all("a", href=True):
    if "website" in link.text.lower() or "agent" in link["href"]:
        token_links.append(link["href"])

# Gefundene Links anzeigen
print("Gefundene Token-Links:")
print(token_links)