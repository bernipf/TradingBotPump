import asyncio
from playwright.async_api import async_playwright
import re

async def fetch_market_cap():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigiere zur gewünschten Seite
        url = "https://pump.fun/coin/CUkqmwqQwvpZpHxCKWiXDFPBL3ceMcetv9yb53zcpump"
        await page.goto(url)
        
        # Wartezeit für das Laden asynchroner Inhalte
        await page.wait_for_timeout(7000)

        # HTML-Inhalt extrahieren
        html_content = await page.content()
        
        # Suche nach Market Cap direkt in HTML-Text
        market_cap_match = re.search(r"market cap:\s*\$([\d,]+)", html_content, re.IGNORECASE)
        
        if market_cap_match:
            market_cap_text = market_cap_match.group(1)
            market_cap_value = int(market_cap_text.replace(",", ""))
            
            print(f"Gefundene Market Cap: {market_cap_value} USD")

            if 9000 <= market_cap_value <= 12000:
                print("Maketcap im gewünschten Bereich")
            else:
                print("Market Cap liegt außerhalb des gewünschten Bereichs.")
        else:
            print("Market Cap-Element nicht gefunden.")

        await browser.close()

# Starte den Market Cap Check
asyncio.run(fetch_market_cap())