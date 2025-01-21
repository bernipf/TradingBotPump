import requests
import time
import random

# API-URL
API_URL = "https://pumpportal.fun/api/trade"

# Liste der API-Keys
API_KEYS = [
    "your-api-key-1",
    "your-api-key-2",
    "your-api-key-3"
]

# Token-Parameter für Raydium
TOKEN_CA = "your CA here"  # Contract Address des Tokens
TRADE_AMOUNT = 100000  # Anzahl an Token
DENOMINATED_IN_SOL = "false"  # "true" für SOL, "false" für Token
SLIPPAGE = 10  # Prozentuale Slippage
PRIORITY_FEE = 0.005  # Zusatzgebühr für schnellere Transaktionen
POOL = "raydium"  # Jetzt Raydium statt Pump

# Trading-Intervall in Sekunden
TRADE_INTERVAL = 60  # Z. B. jede Minute ein Kauf/Verkauf

def trade(action):
    """Kauft oder verkauft den Token über Raydium mit einem zufälligen API-Key."""
    api_key = random.choice(API_KEYS)  # Zufällig einen API-Key auswählen

    response = requests.post(url=API_URL, data={
        "api-key": api_key,
        "action": action,  # "buy" oder "sell"
        "mint": TOKEN_CA,
        "amount": TRADE_AMOUNT,
        "denominatedInSol": DENOMINATED_IN_SOL,
        "slippage": SLIPPAGE,
        "priorityFee": PRIORITY_FEE,
        "pool": POOL  # Raydium als Pool
    })

    try:
        data = response.json()
        if response.status_code == 200 and "error" not in data:
            print(f"{action.capitalize()} erfolgreich auf Raydium! Tx Signature: {data}")
        else:
            print(f"Fehler beim {action} mit API-Key {api_key}: {data}")
    except Exception as e:
        print(f"Fehler bei der API-Anfrage mit API-Key {api_key}: {e}")

# Loop für regelmäßigen Handel
while True:
    print("Starte Kauf auf Raydium...")
    trade("buy")
    time.sleep(TRADE_INTERVAL)

    print("Starte Verkauf auf Raydium...")
    trade("sell")
    time.sleep(TRADE_INTERVAL)