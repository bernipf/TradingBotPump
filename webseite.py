import nest_asyncio
nest_asyncio.apply()

import asyncio
from playwright.async_api import async_playwright
from selenium import webdriver
from bs4 import BeautifulSoup

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
            return token_links
        else:
            print("Keine Token-Links gefunden.")
            return []

# Endlosschleife bis eine Token-Website gefunden wird
def fetch_token_website():
    while True:
        # Token Links abrufen
        loop = asyncio.get_event_loop()
        token_links = loop.run_until_complete(fetch_tokens())

        if token_links:
            # Ersten Link aus den gefundenen Tokens verwenden
            urltoken = token_links[0]

            # Browser-Optionen konfigurieren
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Unsichtbarer Modus
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Browser starten
            driver = webdriver.Chrome(options=options)

            # Token-Seite laden
            driver.get(urltoken)

            # HTML-Inhalt der Seite abrufen
            html = driver.page_source

            # HTML analysieren
            soup = BeautifulSoup(html, "html.parser")

            # Token-Links extrahieren
            token_website = []
            for link in soup.find_all("a", href=True):
                if "website" in link.text.lower() or "agent" in link["href"]:
                    token_website.append(link["href"])

            # Wenn eine Website gefunden wurde, die Schleife beenden
            if token_website:
                print("Gefundene Token-Website:")
                print(token_website)
                break
            else:
                print("Keine Token-Website gefunden, versuche es erneut...")

# Funktion aufrufen
fetch_token_website()