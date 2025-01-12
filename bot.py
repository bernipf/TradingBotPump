import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# Funktion zum Abrufen der ersten Token-URL
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

# Funktion zur Extraktion der Website und des Tickers
async def fetch_token_website_and_ticker():
    while True:  # Endlosschleife
        token_links = await fetch_tokens()
        
        if not token_links:
            print("Keine Token-Links gefunden, versuche es erneut...")
            await asyncio.sleep(5)  # Wartezeit vor erneutem Abrufen
            continue

        # Verwende den ersten gefundenen Token-Link
        urltoken = token_links[0]
        print(f"Verwende Token-URL: {urltoken}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(urltoken)
            
            # Wartezeit für das Laden der Inhalte
            await page.wait_for_timeout(2000)
            
            # Extrahiere Website-Links
            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")

            token_website = None
            for link in soup.find_all("a", href=True):
                if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                    token_website = link["href"]
                    break

            if token_website:
                print("Gefundene Token-Website:", token_website)
                
                # Extrahiere den Ticker aus dem Seitentitel
                title = await page.title()
                match = re.search(r"\((.*?)\)", title)
                ticker = match.group(1) if match else "Kein Ticker gefunden"
                print("Gefundener Ticker:", ticker)
                
                await browser.close()
                break  # Beende die Schleife, wenn ein Token mit Website gefunden wurde
            else:
                print("Keine Token-Website gefunden, versuche es erneut...")
            
            await browser.close()

# Starten der asynchronen Funktion
asyncio.run(fetch_token_website_and_ticker())
