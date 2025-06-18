import requests
import json
from pathlib import Path

# ========================================
# Configuração das credenciais Amadeus
# ========================================
API_KEY    = "ve7uvr5Yoi1GlheZkdkxI8oB0YGpyGPk"
API_SECRET = "hZ7Kf1vS2HFZNFt7"

# ========================================
# Passo 1: Obtenção do OAuth2 Access Token
# ========================================
token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
token_data = {
    "grant_type":    "client_credentials",
    "client_id":     API_KEY,
    "client_secret": API_SECRET
}

token_resp = requests.post(token_url, data=token_data)
token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]

# ========================================
# Passo 2: Consulta de ofertas de voos
# ========================================
search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
headers = {
    "Authorization": f"Bearer {access_token}"
}
params = {
    "originLocationCode":      "GYN",        # Goiânia
    "destinationLocationCode": "MCO",        # Orlando
    "departureDate":           "2025-06-20",
    "returnDate":              "2025-06-28",
    "adults":                  1,
    "currencyCode":            "USD",
    "max":                      50         # Máximo de ofertas retornadas
}

search_resp = requests.get(search_url, headers=headers, params=params)
search_resp.raise_for_status()
offers = search_resp.json()

# ========================================
# Passo 3: Salvando resultado em arquivo
# ========================================
output_path = Path("data/raw/precos_amadeus.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(offers, ensure_ascii=False, indent=2))

print(f"[OK] {len(offers.get('data', []))} ofertas salvas em {output_path}")
