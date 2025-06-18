import requests, json
from pathlib import Path

API_TOKEN = "65eeb5f69123433b74da36c9e0aea0ed"
BASE_URL  = "https://api.travelpayouts.com/v2"

# ===== PARÂMETROS para /prices/month-matrix =====
origin      = "GYN"           # Goiânia
destination = "MCO"           # Orlando
params = {
    "origin":             origin,
    "destination":        destination,
    "month":              "2025-06-01",      # **OBRIGATÓRIO**: primeiro dia do mês
    "currency":           "USD",
    "show_to_affiliates": True,               # obrigatório para parceiros
    "token":              API_TOKEN
}

# ===== CHAMA A API =====
url = f"{BASE_URL}/prices/month-matrix"
resp = requests.get(url, params=params)
try:
    resp.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"[ERRO] HTTP {resp.status_code}: {resp.text}")
    raise

payload = resp.json()
if not payload.get("success", False):
    raise RuntimeError(f"API retornou erro: {json.dumps(payload, indent=2)}")

# ===== EXTRAI os preços por dia =====
#
# payload["data"] vem como lista de objetos, ex:
# [
#   {
#     "origin": "GYN",
#     "destination": "MCO",
#     "depart_date": "2025-06-05",
#     "return_date": "2025-06-12",
#     "value": 450,
#     "number_of_changes": 1,
#     "found_at": "2025-05-01T12:34:56Z",
#     ...
#   },
#   ...
# ]
voos = []
for item in payload["data"]:
    voos.append({
        "origem":      item["origin"],
        "destino":     item["destination"],
        "data_ida":    item["depart_date"],
        "data_volta":  item.get("return_date", ""),
        "preco":       f"{item['value']} {payload['currency']}",
        "paradas":     item.get("number_of_changes", 0),
        "registro":    item.get("found_at")
    })

# ===== SALVA EM JSON =====
out = Path("data/raw/precos_travelpayouts_month_matrix.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(voos, ensure_ascii=False, indent=2))

print(f"[OK] {len(voos)} registros salvos em {out}")
