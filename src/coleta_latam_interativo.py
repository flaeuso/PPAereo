import os
import time
import json
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


def iniciar_driver():
    chrome_options = Options()
    # NÃO usar headless, simular usuário real
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Disfarçar como navegador humano
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver


def coletar_voos_automatizado(origem="São Paulo (GRU)", destino="Rio de Janeiro (SDU)", data="20/07/2025"):
    url = "https://www.latamairlines.com/br/pt"
    driver = iniciar_driver()
    driver.get(url)
    print("[INFO] Página inicial aberta.")

    try:
        wait = WebDriverWait(driver, 40)

        # Campo origem
        origem_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Origem')]")))
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

        # Campo data (abre calendário)
        data_input = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Ida')]")
        data_input.click()
        time.sleep(1)

        # Seleciona a data pelo valor do atributo data-id (ajuste conforme necessidade)
        # ou simula manualmente com tab + enter
        data_parts = data.split("/")
        dia, mes, ano = data_parts
        data_entrada = f"{ano}-{mes}-{dia}"
        driver.execute_script(f'''
            let dateInput = document.querySelector("input[placeholder='Ida']");
            dateInput.value = "{data}";
            dateInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ''')

        time.sleep(2)

        # Clica fora para fechar o calendário
        destino_input.click()
        time.sleep(1)

        # Clica em buscar voos
        buscar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Buscar voos')]")))
        buscar_btn.click()

        print("[INFO] Buscando voos...")

        # Espera os preços aparecerem
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'R$')]")))
        time.sleep(5)

        # Extrai preços visíveis
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

        # Salvar JSON
        if not os.path.exists("data/raw"):
            os.makedirs("data/raw")

        df = pd.DataFrame(voos)
        df.to_json("data/raw/precos_voos_latam.json", orient="records", indent=2, force_ascii=False)
        print(f"[INFO] {len(voos)} voos coletados e salvos.")

    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    coletar_voos_automatizado()

