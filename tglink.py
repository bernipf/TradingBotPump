import asyncio
from playwright.async_api import async_playwright
import json
import re

async def fetch_telegram_profile(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Website aufrufen und warten, bis die Seite geladen ist
        await page.goto(url)
        await page.wait_for_timeout(5000)

        # Suche in allen Skript-Tags nach JSON-Inhalten
        script_elements = await page.query_selector_all("script")
        telegram_url = None

        for element in script_elements:
            content = await element.inner_text()
            
            # Überprüfe, ob im JSON Telegram-URLs vorhanden sind
            if "telegram" in content:
                telegram_match = re.search(r'https://t\.me/[^\"]+', content)
                if telegram_match:
                    telegram_url = telegram_match.group(0)
                    break

        await browser.close()

        if telegram_url:
            print(f"Gefundene Telegram-URL: {telegram_url}")
        else:
            print("Keine Telegram-URL gefunden.")

# Beispielseite aufrufen
url = "https://pump.fun/coin/32XzwkJ74QWNVs4Y78xiZgK7VAAk9KNFYsZf7NiWpump"  # Ersetze durch die tatsächliche URL
asyncio.run(fetch_telegram_profile(url))