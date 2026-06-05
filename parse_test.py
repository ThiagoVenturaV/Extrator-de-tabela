import re

text_output = """Secretaria de Educação e Esporte
GOVERNO DE PERNAMBUCO
ESTADO DE MUDANÇA

COMPROVANTE DE ENTREGA
nº 138.2025

SECRETARIA DE EDUCAÇÃO DE PERNAMBUCO
Dados da transferência

Destino: Escola de Referência em Ensino Médio Prof. Mardônio de
Andrade Lima Coelho
Demandante: GSTE
Código MEC: 26128721
GRE: Recife Norte
Bairro: Bomba do Hemetério
End. Entrega: Rua Chã de Alegria, 117
Cidade: Recife"""

html_table = """<table><thead><tr><th>Contrato nº</th><th>Descrição do material</th><th>Unidade</th><th>Quantidade</th><th>Tombamento</th></tr></thead><tbody><tr><td>083/2024</td><td>Notebook Positivo Para Laboratório Móvel</td><td>Und.</td><td>45</td><td>2024101017824 À 2024101017868</td></tr></tbody></table>"""

# Parse Destino
destino_match = re.search(r'Destino:\s*(.*?)\s*\n(?:Demandante|Código MEC|GRE|Bairro|End)', text_output, re.DOTALL | re.IGNORECASE)
destino = destino_match.group(1).replace('\n', ' ').strip() if destino_match else ""

# Parse MEC
mec_match = re.search(r'Código MEC:\s*(\d+)', text_output, re.IGNORECASE)
mec = mec_match.group(1).strip() if mec_match else ""

print(f"Parsed Destino: '{destino}'")
print(f"Parsed MEC: '{mec}'")

# Parse HTML Table rows
tbody_match = re.search(r'<tbody>(.*?)</tbody>', html_table, re.DOTALL | re.IGNORECASE)
if tbody_match:
    tbody_content = tbody_match.group(1)
    trs = re.findall(r'<tr>(.*?)</tr>', tbody_content, re.DOTALL | re.IGNORECASE)
    for tr in trs:
        tds = re.findall(r'<td>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
        print(f"Parsed Row: {tds}")
else:
    print("No tbody found")
