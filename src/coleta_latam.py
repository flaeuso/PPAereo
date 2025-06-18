import time
import json
import pandas as pd
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def iniciar_driver():
    chrome_options = Options()

    # ❌ NÃO usar headless para evitar bloqueio
    # chrome_options.add_argument("--headless=new")

    # ✅ Simulação de comportamento humano
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")

    # ✅ User-Agent de navegador real
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Remover traços de automação
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    return driver


def coletar_precos(origem='GRU', destino='SDU', data_ida='20/07/2025'):
    url = f'https://www.latamairlines.com/br/pt/ofertas-voos?origin={origem}&destination={destino}&outboundDate={data_ida}&tripType=oneWay'
    driver = iniciar_driver()
    driver.get(url)

    print(f"[INFO] Acessando URL: {url}")

    try:
        # Aguarda até que pelo menos 1 preço apareça
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'R$')]"))
        )
    except Exception as e:
        print(f"[ERRO] Timeout ou página bloqueada: {e}")
        driver.save_screenshot("screenshot_erro.png")
        driver.quit()
        return

    time.sleep(5)  # garante carregamento completo após aparecer os elementos

    voos = []

    try:
        # Tente capturar pelo preço visível
        precos = driver.find_elements(By.XPATH, "//span[contains(text(),'R$')]")

        for i, preco_elem in enumerate(precos):
            try:
                preco = preco_elem.text.strip()
                voo = {
                    'origem': origem,
                    'destino': destino,
                    'data': data_ida,
                    'horario': f"Horário simulado {i+1}",
                    'preco': preco
                }
                voos.append(voo)
            except Exception as e:
                print(f"[WARN] erro parcial: {e}")
                continue

    finally:
        driver.quit()

    if not os.path.exists("data/raw"):
        os.makedirs("data/raw")

    df = pd.DataFrame(voos)
    print(df)

    output_path = 'data/raw/precos_voos_latam.json'
    df.to_json(output_path, orient='records', indent=2, force_ascii=False)
    print(f"[INFO] {len(voos)} voos coletados e salvos em {output_path}")


if __name__ == '__main__':
    coletar_precos()

