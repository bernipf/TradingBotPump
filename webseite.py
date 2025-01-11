from selenium import webdriver

# Browser-Optionen konfigurieren
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Unsichtbarer Modus
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Browser starten
driver = webdriver.Chrome(options=options)

# Pump.fun-Seite laden
url = "https://pump.fun/coin/2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump"
driver.get(url)

# HTML-Inhalt der Seite abrufen
html = driver.page_source

from bs4 import BeautifulSoup

# HTML analysieren
soup = BeautifulSoup(html, "html.parser")

# Token-Links extrahieren
token_links = []
for link in soup.find_all("a", href=True):
    if "website" in link.text.lower() or "agent" in link["href"]:
        token_links.append(link["href"])

# Gefundene Links anzeigen
print("Gefundene Token-Links:")
print(token_links)
