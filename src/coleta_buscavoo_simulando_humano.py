import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def coletar_voos_com_simulacao():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()

        print("[INFO] Acessando página inicial do BuscaVoo...")
        await page.goto("https://www.buscavoo.com.br/")
        await page.wait_for_timeout(3000)

        # Função auxiliar para preencher Selectize.js e selecionar com teclado
        async def selectize_choose(container_nth: int, text: str):
            container = page.locator('div.selectize-input.items:not(.full)').nth(container_nth)
            input_field = container.locator('input')
            # Clica e abre dropdown
            await input_field.click()
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(200)
            # Digita o texto
            await page.keyboard.type(text, delay=100)
            # Seleciona a primeira sugestão
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(500)

        print("[INFO] Preenchendo Origem...")
        await selectize_choose(0, "Goiânia")

        print("[INFO] Preenchendo Destino...")
        await selectize_choose(1, "Orlando")

        print("[INFO] Selecionando datas de ida e volta...")
        # Data de ida
        await page.click('#calendarDeparture')
        await page.keyboard.type("21/06/2025", delay=50)
        await page.keyboard.press("Enter")
        await page.keyboard.press("Enter")
        # Data de volta
        await page.click('#calendarReturn')
        await page.keyboard.type("28/06/2025", delay=50)
        await page.keyboard.press("Enter")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(500)

        print("[INFO] Clicando em Buscar...")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(5000)

        print("[INFO] Extraindo resultados...")
        cards = await page.query_selector_all(".flight-info-container")
        voos = []
        for card in cards:
            try:
                preco = await card.query_selector_eval(".flight-price", "el => el.textContent.trim()")
                companhia = await card.query_selector_eval(".airline-name", "el => el.textContent.trim()")
                horarios = await card.query_selector_all(".flight-time")
                ida = await horarios[0].inner_text()
                volta = await horarios[1].inner_text()
                voos.append({
                    "companhia": companhia,
                    "preco": preco,
                    "ida": ida,
                    "volta": volta
                })
            except Exception as e:
                print(f"[WARN] Erro ao extrair card: {e}")

        print(f"[INFO] {len(voos)} voos coletados")
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        with open("data/raw/precos_voos_buscavoo.json", "w", encoding="utf-8") as f:
            json.dump(voos, f, indent=2, ensure_ascii=False)
        print("[OK] Dados salvos em data/raw/precos_voos_buscavoo.json")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(coletar_voos_com_simulacao())
