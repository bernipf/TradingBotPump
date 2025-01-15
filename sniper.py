import asyncio
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re

# URL zur Überwachung
URL_TO_MONITOR = "https://pump.fun/advanced"

# Benutzerdefinierter Token-Name und Ticker zur Überprüfung
target_token_name = input("Bitte geben Sie den zu überwachenden Token-Namen ein: ")
target_ticker = input("Bitte geben Sie den zu überwachenden Ticker ein: ")

# Funktion für den automatisierten Kauf über die PumpPortal API
def perform_purchase_api(mint_address, amount):
    api_key = "ct6njcu6855pgp9j9ru6ggkua9cm8c2hdwv3arvq9514yvk5ah0p4kbadxgpmcu8exx50wj7998mcrjpddkpapk8dta4gdvbadx72wk4err56rujdxjmmmbbdnk72auge1u2ydk6ewykuf9m6ebtg5dt4gxj79npkedtb6489d32nhfeh76akb6c58kgm2pata78t3k8x8kuf8"  # Setze deinen API-Schlüssel ein

    # Definiere die Payload für die API-Anfrage
    payload = {
        "action": "buy",  # Aktion, hier 'buy' für Kauf
        "mint": mint_address,  # Die Contract-Adresse des Tokens, den du kaufen möchtest
        "amount": amount,  # Menge der Tokens (z.B. Anzahl der Tokens, die du kaufen möchtest)
        "denominatedInSol": "true",  # 'false', da wir mit Token und nicht SOL arbeiten
        "slippage": 100,  # Erlaubter Slippage (in Prozent)
        "priorityFee": 0.005,  # Gebühr zur Beschleunigung der Transaktion
        "pool": "pump"  # Börse, auf der gehandelt werden soll (z.B. "pump" oder "raydium")
    }

    try:
        # Sende die POST-Anfrage an die API
        response = requests.post(url="https://pumpportal.fun/api/trade?api-key=" + api_key, data=payload)
        
        # Parsen der Antwort der API
        data = response.json()

        if response.status_code == 200 and "txSignature" in data:
            print(f"Kauf erfolgreich! Transaktions-Signatur: {data['txSignature']}")
        else:
            print(f"Fehler beim Kauf: {data.get('error', 'Unbekannter Fehler')}")
    
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der API-Anfrage: {e}")

# Funktion zum Extrahieren der Contract-Adresse aus dem Token-Link
def extract_mint_address_from_link(token_link):
    # Die Contract-Adresse befindet sich im letzten Teil des Links nach "/coin/"
    match = re.search(r"/coin/([^/]+)", token_link)
    return match.group(1) if match else None

# Funktion zum Abrufen des neuesten Token-Links
async def fetch_latest_token_link(page):
    await page.goto(URL_TO_MONITOR)
    await page.wait_for_selector("tbody[data-testid='virtuoso-item-list']")

    elements = await page.query_selector_all("tbody[data-testid='virtuoso-item-list'] a")
    for element in elements:
        href = await element.get_attribute("href")
        if href and "/coin/" in href:
            return f"https://pump.fun{href}"
    return None

# Funktion zum Extrahieren des Token-Namens und Tickern von der Zielseite
async def extract_token_details(page):
    html_content = await page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Extrahieren des Token-Namens aus dem Titel
    title = soup.title.string if soup.title else "Kein Titel gefunden"
    name_match = re.search(r"^(.*?)\(", title)
    token_name = name_match.group(1).strip() if name_match else "Kein Token-Name gefunden"

    # Extrahieren des Tickers
    ticker_match = re.search(r"\((.*?)\)", title)
    ticker = ticker_match.group(1) if ticker_match else "Kein Ticker gefunden"

    return token_name, ticker

# Hauptlogik zur Überwachung neuer Token-Links und Kauf
async def monitor_new_tokens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        last_seen_link = None

        while True:
            try:
                print(f"⚡ Überprüfe auf neue Token-Links unter {URL_TO_MONITOR}")
                latest_link = await fetch_latest_token_link(page)

                if latest_link and latest_link != last_seen_link:
                    print(f"Neuer Token-Link entdeckt: {latest_link}")
                    last_seen_link = latest_link

                    # Extrahiere die Mint-Adresse aus dem Token-Link
                    mint_address = extract_mint_address_from_link(latest_link)
                    if mint_address:
                        print(f"Gefundene Contract-Adresse: {mint_address}")
                    else:
                        print("Fehler: Keine Contract-Adresse im Link gefunden.")
                        continue  # Wenn keine Contract-Adresse gefunden wird, überspringe den Token

                    # Gehe zur Token-Seite und extrahiere den Token-Namen und Ticker
                    await page.goto(latest_link)
                    token_name, ticker = await extract_token_details(page)

                    print(f"Gefundener Token-Name: {token_name}")
                    print(f"Gefundener Ticker: {ticker}")

                    if target_token_name.lower() in token_name.lower():
                        print(f"✔ Ziel-Token '{target_token_name}' im Token-Namen '{token_name}' gefunden!")
                    else:
                        print(f"✖ Ziel-Token '{target_token_name}' nicht im Token-Namen '{token_name}' enthalten.")

                    if target_ticker.lower() in ticker.lower():
                        print(f"✔ Ziel-Ticker '{target_ticker}' stimmt mit gefundenem Ticker '{ticker}' überein!")
                    else:
                        print(f"✖ Ziel-Ticker '{target_ticker}' stimmt nicht mit gefundenem Ticker '{ticker}' überein.")

                    # Menge der Tokens, die gekauft werden sollen
                    amount_to_buy = 2.5  # Beispiel für eine Kaufmenge

                    # Kaufe den Token über die API, wenn Name und Ticker übereinstimmen
                    if target_token_name.lower() in token_name.lower() and target_ticker.lower() in ticker.lower():
                        perform_purchase_api(mint_address, amount_to_buy)  # API-Kauf-Funktion

                    # Kehre zur Überwachungsseite zurück
                    await page.goto(URL_TO_MONITOR)

                else:
                    print("Kein neuer Link gefunden. Warte auf nächste Überprüfung...")

            except PlaywrightTimeoutError:
                print("Timeout beim Laden der Seite. Versuche es erneut...")
            except Exception as e:
                print(f"Fehler: {e}")

        await browser.close()

# Starte den Token-Scan
asyncio.run(monitor_new_tokens())