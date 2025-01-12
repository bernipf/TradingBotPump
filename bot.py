import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

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

async def fetch_token_website():
    while True:
        token_links = await fetch_tokens()
        if token_links:
            urltoken = token_links[0]
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(urltoken)

                # Wartezeit, um sicherzustellen, dass Inhalte vollständig geladen sind
                await page.wait_for_timeout(2000)

                # Extrahiere und analysiere den HTML-Inhalt der Seite
                html_content = await page.content()
                soup = BeautifulSoup(html_content, "html.parser")

                # Suche nach Links mit relevanten Attributen oder Texten
                token_website = None
                for link in soup.find_all("a", href=True):
                    if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                        token_website = link["href"]
                        break

                if token_website:
                    print("Gefundene Token-Website:")
                    print(token_website)
                    print("Pump:")
                    print(token_links[0])
                    break
                else:
                    print("Keine Token-Website gefunden, versuche es erneut...")

                await browser.close()
        else:
            print("Keine Token-Links gefunden, versuche es erneut...")
        await asyncio.sleep(10)

# Starten der asynchronen Funktion
asyncio.run(fetch_token_website())
