import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import re

# Punktwerte für die Keywords
keyword_scores = {
    "tokenomics": 1,
    "roadmap": 2,
    "ai": 1,
}

# Funktion zum Abrufen der Token-Links
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

# Funktion zur Suche der Token-Website und Ticker-Extraktion
async def fetch_token_website_and_ticker():
    while True:  # Endlosschleife
        token_links = await fetch_tokens()
        if not token_links:
            print("Keine Token-Links gefunden, versuche es erneut...")
            await asyncio.sleep(5)
            continue

        urltoken = token_links[0]
        print(f"Verwende Token-URL: {urltoken}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(urltoken)
            await page.wait_for_timeout(2000)

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")

            token_website = None
            for link in soup.find_all("a", href=True):
                if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                    token_website = link["href"]
                    break

            if token_website:
                print("Gefundene Token-Website:", token_website)

                # Ticker aus Seitentitel extrahieren
                title = await page.title()
                match = re.search(r"\((.*?)\)", title)
                ticker = match.group(1) if match else "Kein Ticker gefunden"
                print("Gefundener Ticker:", ticker)

                # Führe Keyword-Analyse durch
                score = keyword_analysis(token_website, ticker)
                print(f"Gesamtpunktzahl für '{ticker}': {score}")
                
                await browser.close()
                break
            else:
                print("Keine Token-Website gefunden, versuche es erneut...")
            
            await browser.close()

        await asyncio.sleep(5)

# Funktion zur Keyword-Analyse
def keyword_analysis(url, token_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text.lower()

        total_score = 0
        for keyword, points in keyword_scores.items():
            if keyword in html_content:
                total_score += points
                print(f"Gefunden: '{keyword}', Punkte: {points}")

        if token_name.lower() not in html_content:
            print(f"Warnung: Token-Name '{token_name}' nicht gefunden.")
            total_score -= 3

        return total_score
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Website: {e}")
        return -10

# Starte das Programm
asyncio.run(fetch_token_website_and_ticker())