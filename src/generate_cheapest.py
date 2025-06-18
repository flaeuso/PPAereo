import json
from pathlib import Path


def load_raw_offers(json_path: str):
    """
    Carrega o JSON completo de ofertas da Amadeus (keys: 'meta', 'data').
    Retorna a lista resp['data'].
    """
    resp = json.loads(Path(json_path).read_text(encoding="utf-8"))
    offers = resp.get('data', [])
    return offers


def simplify_offers(offers: list):
    """
    Converte cada oferta bruta no formato simplificado:
    {'offerId': ..., 'price': ..., 'currency': ...}
    """
    simplified = []
    for offer in offers:
        price_info = offer.get('price', {})
        total = price_info.get('total')
        currency = price_info.get('currency')
        simplified.append({
            'offerId': offer.get('id'),
            'price': float(total) if total is not None else float('inf'),
            'currency': currency
        })
    return simplified


def generate_html(offers: list, output_file: str):
    """
    Gera um arquivo HTML listando as 3 opções mais baratas.
    """
    html_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>3 Opções Mais Baratas - GYN → MCO</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
    </style>
</head>
<body>
    <h1>3 Opções Mais Baratas - GYN → MCO</h1>
    <table>
        <thead>
            <tr><th>#</th><th>ID da Oferta</th><th>Preço</th></tr>
        </thead>
        <tbody>
{rows}
        </tbody>
    </table>
</body>
</html>'''

    rows_html = []
    for idx, offer in enumerate(offers[:3], start=1):
        preco_str = f"{offer['price']:.2f} {offer['currency']}"
        rows_html.append(f"            <tr><td>{idx}</td><td>{offer['offerId']}</td><td>{preco_str}</td></tr>")
    rows_str = "\n".join(rows_html)

    final_html = html_template.format(rows=rows_str)
    Path(output_file).write_text(final_html, encoding="utf-8")
    print(f"[OK] Página de saída gerada: {output_file}")


if __name__ == '__main__':
    # Caminho para o JSON completo de ofertas da Amadeus
    json_input = 'data/raw/precos_amadeus.json'
    output_html = 'data/output/3_opcoes_mais_baratas.html'

    # Carrega e simplifica
    raw_offers = load_raw_offers(json_input)
    simple = simplify_offers(raw_offers)

    # Ordena e gera HTML
    sorted_offers = sorted(simple, key=lambda x: x['price'])
    Path(output_html).parent.mkdir(parents=True, exist_ok=True)
    generate_html(sorted_offers, output_html)
