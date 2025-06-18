import os
import time
import json
import pandas as pd

from selenium.webdriver import Edge, EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def iniciar_driver():
    options = EdgeOptions()
    options.use_chromium = True
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    service = EdgeService(EdgeChromiumDriverManager().install())
    driver = Edge(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })

    return driver


def coletar_voos_edge(origem="São Paulo (GRU)", destino="Rio de Janeiro (SDU)", data="20/07/2025"):
    url = "https://www.latamairlines.com/br/pt"
    driver = iniciar_driver()
    driver.get(url)
    print("[INFO] Página da LATAM carregada.")

    try:
        wait = WebDriverWait(driver, 30)

        # Aguarda o campo de origem
        origem_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Origem')]"))
        )
        origem_input.clear()
        origem_input.send_keys(origem)
        time.sleep(2)
        origem_input.send_keys(Keys.DOWN, Keys.ENTER)

        # Campo destino
        destino_input = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Destino')]")
        destino_input.clear()
        destino_input.send_keys(destino)
        time.sleep(2)
        destino_input.send_keys(Keys.DOWN, Keys.ENTER)

        # Campo de data de ida
        data_input = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Ida')]")
        data_input.click()
        time.sleep(2)
        driver.execute_script(f'''
            let input = document.querySelector("input[placeholder='Ida']");
            input.value = "{data}";
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ''')

        # Fecha calendário clicando fora
        destino_input.click()
        time.sleep(1)

        # Clica em buscar voos
        buscar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Buscar voos')]")))
        buscar_btn.click()
        print("[INFO] Buscando voos...")

        # Espera preços
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'R$')]")))
        time.sleep(5)

        precos = driver.find_elements(By.XPATH, "//span[contains(text(),'R$')]")
        voos = []
        for i, preco_elem in enumerate(precos):
            preco = preco_elem.text.strip()
            voos.append({
                "origem": origem,
                "destino": destino,
                "data": data,
                "horario": f"Horário {i+1}",
                "preco": preco
            })

        # Salva os dados
        os.makedirs("data/raw", exist_ok=True)
        df = pd.DataFrame(voos)
        df.to_json("data/raw/precos_voos_latam.json", orient="records", indent=2, force_ascii=False)
        print(f"[INFO] {len(voos)} voos coletados e salvos com sucesso.")

    except Exception as e:
        print(f"[ERRO] Falha na execução: {e}")
        driver.save_screenshot("screenshot_falha.png")
        print("[INFO] Screenshot salvo como screenshot_falha.png para depuração.")

    finally:
        driver.quit()


if __name__ == "__main__":
    coletar_voos_edge()
