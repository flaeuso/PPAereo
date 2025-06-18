# src/api.py

from fastapi import FastAPI, Query
from typing import Optional, List
import json
import os

app = FastAPI()

ARQUIVO_DADOS = "data/raw/precos_voos_latam.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return []
    with open(ARQUIVO_DADOS, encoding='utf-8') as f:
        return json.load(f)

@app.get("/")
def raiz():
    return {"mensagem": "API de Preços de Voos - LATAM"}

@app.get("/voos")
def listar_voos(
    origem: Optional[str] = Query(None),
    destino: Optional[str] = Query(None),
    data: Optional[str] = Query(None),
    preco_min: Optional[float] = Query(None)
):
    dados = carregar_dados()
    resultados = []

    for voo in dados:
        preco_float = float(voo['preco'].replace("R$", "").replace(",", ".").strip())

        if origem and origem != voo["origem"]:
            continue
        if destino and destino != voo["destino"]:
            continue
        if data and data != voo["data"]:
            continue
        if preco_min and preco_float < preco_min:
            continue

        voo["preco_float"] = preco_float
        resultados.append(voo)

    return {"total": len(resultados), "voos": resultados}

@app.get("/favicon.ico")
async def favicon():
    return {}

