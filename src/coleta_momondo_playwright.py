import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

# Parâmetros de busca
ORIGEM = "GYN"       # Código IATA Goiânia
DESTINO = "MCO"      # Código IATA Orlando
DATA_IDA = "20-06-2025"  # Formato DD-MM-YYYY
DATA_VOLTA = "28-06-2025"

# Monta URL de busca Momondo
URL = (
    "https://www.momondo.com/flightsearch?Search=true&TripType=2&SegNo=2"
    f"&SO0={ORIGEM}&SD0={DESTINO}&SDP0={DATA_IDA}"
    f"&SO1={DESTINO}&SD1={ORIGEM}&SDP1={DATA_VOLTA}"
    "&AD=1&CH=0&IN=0"
)

# Saída
OUT_DIR = Path("data/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "precos_momondo.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = await context.new_page()
        print(f"[INFO] Navegando para {URL}...")
        await page.goto(URL)

        # Espera os resultados carregarem
        await page.wait_for_selector(".resultWrapper", timeout=60000)
        # Pequena pausa adicional
        await page.wait_for_timeout(5000)

        # Extrai dados
        cards = await page.query_selector_all(".resultWrapper")
        voos = []
        for card in cards:
            try:
                preco_el = await card.query_selector(".price")
                cia_el = await card.query_selector(".airlineName")
                time_el = await card.query_selector_all(".routeInfo .time")
                preco = (await preco_el.inner_text()).strip() if preco_el else None
                cia = (await cia_el.inner_text()).strip() if cia_el else None
                ida = (await time_el[0].inner_text()).strip() if len(time_el) > 0 else None
                volta = (await time_el[1].inner_text()).strip() if len(time_el) > 1 else None
                if preco and cia:
                    voos.append({
                        "companhia": cia,
                        "preco": preco,
                        "ida": ida,
                        "volta": volta
                    })
            except Exception:
                continue

        # Salva JSON
        OUT_FILE.write_text(json.dumps(voos, ensure_ascii=False, indent=2))
        print(f"[OK] {len(voos)} voos salvos em {OUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
