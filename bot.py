import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import re

# Punktwerte für die Keywords
keyword_scores = {
    "tokenomics": 1,
    "roadmap": 2,
}

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

async def fetch_token_website_and_socials():
    while True:
        token_links = await fetch_tokens()
        if token_links:
            urltoken = token_links[0]
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(urltoken)
                await page.wait_for_timeout(5000)

                html_content = await page.content()
                soup = BeautifulSoup(html_content, "html.parser")

                # Suche nach der Token-Website
                token_website = None
                for link in soup.find_all("a", href=True):
                    if any(keyword in link.text.lower() for keyword in ["website", "official"]) or "agent" in link["href"]:
                        token_website = link["href"]
                        break

                # Suche nach der Twitter-URL
                twitter_url = None
                script_elements = await page.query_selector_all("script")
                for element in script_elements:
                    content = await element.inner_text()
                    if "twitter" in content:
                        twitter_match = re.search(r'https://x\.com/[^\"]+', content)
                        if twitter_match:
                            twitter_url = twitter_match.group(0)
                            break

                # Suche nach der Telegram-URL
                telegram_url = None
                for element in script_elements:
                    content = await element.inner_text()
                    if "telegram" in content:
                        telegram_match = re.search(r'https://t\.me/[^\"]+', content)
                        if telegram_match:
                            telegram_url = telegram_match.group(0)
                            break

                await browser.close()

                if token_website:
                    print(f"Gefundene Token-Website: {token_website}")
                    print(f"Pump-Link: {urltoken}")

                    # Ticker extrahieren
                    title = soup.title.string if soup.title else "Kein Titel gefunden"
                    ticker_match = re.search(r"\((.*?)\)", title)
                    ticker = ticker_match.group(1) if ticker_match else "Kein Ticker gefunden"
                    print(f"Gefundener Ticker: {ticker}")

                    # Keyword-Analyse auf der Token-Website
                    score = keyword_analysis(token_website, ticker)
                    print(f"Gesamtpunktzahl: {score}")

                    if twitter_url:
                        print(f"Gefundene Twitter-URL: {twitter_url}")
                    if telegram_url:
                        print(f"Gefundene Telegram-URL: {telegram_url}")

                    break
                else:
                    print("Keine Token-Website gefunden, versuche es erneut...")

        else:
            print("Keine Token-Links gefunden, versuche es erneut...")
        await asyncio.sleep(10)

def keyword_analysis(url, token_name):
    response = requests.get(url)
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

# Starte den Token-Scan
asyncio.run(fetch_token_website_and_socials())