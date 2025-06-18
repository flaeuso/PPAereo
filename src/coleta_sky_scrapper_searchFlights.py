import requests, json
from pathlib import Path

# ===== CONFIGURAÇÃO RAPIDAPI =====
HOST = "sky-scrapper.p.rapidapi.com"
KEY  = "84ff6f8667mshdfd29c5b05db3eap16b66ajsnd93f7e1d9236"
HEADERS = {
    "x-rapidapi-host": HOST,
    "x-rapidapi-key":  KEY,
    "Content-Type":    "application/json"
}
COMMON_PARAMS = {
    "locale":      "en-US",
    "market":      "en-US",
    "countryCode":"US"
}

def lookup_location(query):
    """Chama /api/v2/flights/locations para obter skyId e entityId."""
    url = f"https://{HOST}/api/v2/flights/locations"
    params = {**COMMON_PARAMS, "query": query}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()
    if not data.get("status", True):
        raise RuntimeError("Lookup falhou: " + json.dumps(data, indent=2))
    loc = data["message"][0]
    # message[0] traz { skyId, entityId, name, ... }
    return loc["skyId"], loc["entityId"]

def search_flights(orig, dest, dep_date, ret_date):
    """Chama /api/v2/flights/searchFlights com os parâmetros corretos."""
    originSky,  originEnt  = lookup_location(orig)
    destSky,    destEnt    = lookup_location(dest)

    params = {
        **COMMON_PARAMS,
        "originSkyId":         originSky,
        "destinationSkyId":    destSky,
        "originEntityId":      originEnt,
        "destinationEntityId": destEnt,
        "departureDate":       dep_date,    # YYYY-MM-DD
        "returnDate":          ret_date,    # YYYY-MM-DD
        "cabinClass":          "economy",
        "adults":              1,
        "sortBy":              "best",
        "currency":            "USD"
    }

    url = f"https://{HOST}/api/v2/flights/searchFlights"
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()
    if not data.get("status", True):
        raise RuntimeError("Search falhou: " + json.dumps(data, indent=2))
    return data

def main():
    # Exemplo: Londres → New York City
    ORIG = "London"
    DEST = "New York City"
    DEP  = "2024-04-11"
    RET  = "2024-04-18"

    print(f"[1/2] Resolvendo IDs para “{ORIG}” e “{DEST}”…")
    skyO, entO = lookup_location(ORIG)
    skyD, entD = lookup_location(DEST)
    print(f" → {ORIG}: skyId={skyO}, entityId={entO}")
    print(f" → {DEST}: skyId={skyD}, entityId={entD}")

    print(f"[2/2] Buscando voos de {ORIG} → {DEST} ({DEP}→{RET})…")
    result = search_flights(ORIG, DEST, DEP, RET)

    out = Path("data/raw/precos_sky_scrapper_searchFlights.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[OK] Dados salvos em {out}")

if __name__ == "__main__":
    main()
