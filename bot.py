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