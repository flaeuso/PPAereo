from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import json
from pathlib import Path

app = FastAPI()

# Amadeus credentials\NAME_
AMADEUS_CLIENT_ID = "ve7uvr5Yoi1GlheZkdkxI8oB0YGpyGPk"
AMADEUS_CLIENT_SECRET = "hZ7Kf1vS2HFZNFt7"
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# HTML form template
HTML_FORM = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Busca de Passagens</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    label { display: block; margin-top: 10px; }
    input { padding: 5px; width: 200px; }
    button { margin-top: 15px; padding: 10px 20px; }
  </style>
</head>
<body>
  <h1>Extrator de Passagens - Amadeus API</h1>
  <form action="/search" method="get">
    <label>Origem (IATA): <input name="origin" value="GYN" required></label>
    <label>Destino (IATA): <input name="destination" value="MCO" required></label>
    <label>Data de Ida (YYYY-MM-DD): <input name="departureDate" value="2025-06-20" required></label>
    <label>Data de Volta (YYYY-MM-DD): <input name="returnDate" value="2025-06-28"></label>
    <label>Passageiros (adultos): <input type="number" name="adults" value="1" min="1"></label>
    <button type="submit">Buscar</button>
  </form>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def form():
    return HTMLResponse(content=HTML_FORM)

@app.get("/search", response_class=HTMLResponse)
async def search(origin: str, destination: str, departureDate: str, returnDate: str = None, adults: int = 1):
    # 1) Get OAuth2 token
    r = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    })
    r.raise_for_status()
    token = r.json().get("access_token", "")

    # 2) Prepare search parameters
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departureDate,
        "adults": adults,
        "currencyCode": "USD"
    }
    if returnDate:
        params["returnDate"] = returnDate

    # 3) Request flight offers
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(OFFERS_URL, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    # 4) Simplify and save minimal JSON in /raw
    offers = data.get("data", [])
    simple = []
    for o in offers:
        seg0 = o.get("itineraries", [{}])[0].get("segments", [{}])[0]
        orig = seg0.get("departure", {}).get("iataCode", "")
        ida = seg0.get("departure", {}).get("at", "")[:10]
        if len(o.get("itineraries", [])) > 1:
            seg1 = o.get("itineraries", [])[1].get("segments", [{}])[0]
            volta = seg1.get("departure", {}).get("at", "")[:10]
        else:
            volta = ""
        price = o.get("price", {}).get("total", "")
        simple.append({
            "origem": orig,
            "destino": destination,
            "data_ida": ida,
            "data_volta": volta,
            "preco": price
        })
    raw = Path("raw")
    raw.mkdir(exist_ok=True)
    out_file = raw / f"precos_{origin}_{destination}.json"
    out_file.write_text(json.dumps(simple, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5) Top 3 cheapest
    for item in simple:
        try:
            item["preco"] = float(item["preco"])
        except:
            item["preco"] = float("inf")
    top3 = sorted(simple, key=lambda x: x["preco"])[:3]

    # 6) Return HTML with only the 3 prices
    list_items = "".join(f"<li>{idx+1}. {r['preco']:.2f}</li>" for idx, r in enumerate(top3))
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Top 3 Preços</title></head>
<body>
  <h2>Top 3 Preços - {origin}→{destination}</h2>
  <ul>
    {list_items}
  </ul>
</body>
</html>"""
    return HTMLResponse(content=html)

# To run:
# uvicorn src.fastapi_app:app --reload --port 8000
