import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def fetch_tokens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://pump.fun/advanced"

        try:
            await page.goto(url)
            # Warte, bis die Token-Tabellen geladen sind
            await page.wait_for_selector("tbody[data-testid='virtuoso-item-list'] a", timeout=10000)

            token_links = []
            elements = await page.query_selector_all("tbody[data-testid='virtuoso-item-list'] a")

            for element in elements:
                href = await element.get_attribute("href")
                if href and "/coin/" in href:
                    token_links.append(f"https://pump.fun{href}")

        except PlaywrightTimeoutError:
            print("Fehler: Zeitüberschreitung beim Laden der Seite.")

        await browser.close()
        return token_links

async def fetch_token_website():
    while True:
        token_links = await fetch_tokens()

        if token_links:
            urltoken = token_links[0]
            print(f"Neuester Token-Link: {urltoken}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    await page.goto(urltoken)
                    # Warte auf vollständige Seitendarstellung
                    await page.wait_for_load_state('domcontentloaded')

                    # Suche nach möglichen Website-Links in eingebetteten Daten oder im Seitentext
                    website_url = await page.evaluate('''
                        () => {
                            let matches = document.body.innerText.match(/"website":"(https?:\/\/[^"]+)"/);
                            return matches ? matches[1] : null;
                        }
                    ''')

                    if website_url:
                        print("Gefundene Token-Website:")
                        print(website_url)
                        break
                    else:
                        print("Keine Token-Website gefunden, versuche es erneut...")
                
                except PlaywrightTimeoutError:
                    print("Fehler beim Laden der Token-Seite.")
                
                await browser.close()
        else:
            print("Keine Token-Links gefunden, versuche es erneut...")
        await asyncio.sleep(10)  # Warte, bevor die nächste Abfrage gestartet wird

# Starten der asynchronen Funktion
asyncio.run(fetch_token_website())
