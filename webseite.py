import requests

# Punktwerte für die Keywords
keyword_scores = {
    "tokenomics": 1,
    "roadmap": 2,
}

def keyword_analysis(url, token_name):
    # HTTP-Request, um den statischen HTML-Code der Seite zu erhalten
    response = requests.get(url)
    html_content = response.text.lower()  # Der gesamte HTML-Quellcode wird als String verwendet

    # Punkteberechnung
    total_score = 0
    for keyword, points in keyword_scores.items():
        # Suche nach dem Keyword im HTML-Quellcode
        if keyword in html_content:
            total_score += points
            print(f"Gefunden: '{keyword}', Punkte: {points}")

    # Überprüfen, ob der Token-Name im HTML-Quelltext enthalten ist
    if token_name.lower() not in html_content:
        print(f"Warnung: Token-Name '{token_name}' nicht gefunden.")
        total_score -= 3  # Beispielpunktabzug, wenn der Name fehlt

    return total_score

# Beispiel-URL und Token-Name für Testzwecke
url = "https://beercoin.wtf"  # Ersetze durch die tatsächliche URL
token_name = "beer"  # Ersetze durch den tatsächlichen Token-Namen

# Keyword-Analyse ausführen
score = keyword_analysis(url, token_name)
print(f"Gesamtpunktzahl: {score}")