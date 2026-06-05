import sys
import time
import json
import base64
import io
import requests
sys.path.insert(0, '.')
from extract_tables import *
from PIL import Image

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5vl:3b"

pdf_path = 'input/Anexo (86992811).pdf'
doc = fitz.open(pdf_path)

page = doc[0]
zoom = 150 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# Rotate 90 degrees CCW to make it upright
img_rotated = img.rotate(90, expand=True)

buffer = io.BytesIO()
img_rotated.save(buffer, format="JPEG", quality=80)
buffer.seek(0)
img_b64 = base64.b64encode(buffer.read()).decode('utf-8')

# Save for visual inspection
import os
os.makedirs('debug_pages', exist_ok=True)
img_rotated.save('debug_pages/page_1_qwen_rot90.png')

print(f"\n--- Testing page 1 with {MODEL} ---")
print(f"Image size: {img_rotated.size}")

prompt = """Look at this scanned document image carefully. It is a "COMPROVANTE DE ENTREGA" (delivery receipt) from the Brazilian government (Secretaria de Educação de Pernambuco).

There should be a table with columns like: Contrato nº, Descrição do material, Unidade, Quantidade, Tombamento.

If there IS a table with data rows, extract ALL rows in this JSON format:
{
  "tem_tabela": true,
  "destino": "school/destination name from the header",
  "codigo_mec": "MEC code number from the header",
  "linhas": [
    {"contrato": "contract number", "descricao": "material description", "quantidade": "quantity", "tombamento": "tombamento number if present"}
  ]
}

If there is NO table with material data (e.g. it's a signature page, blank page, or form without a data table), respond:
{"tem_tabela": false}

RULES:
- Extract ALL rows, do not skip any
- Keep values exactly as they appear
- Empty fields should be ""
- "N/A" is a valid contract value
- Copy tombamento numbers completely
- Respond ONLY with JSON, no extra text"""

payload = {
    "model": MODEL,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {"temperature": 0.1, "num_predict": 4096}
}

start = time.time()
try:
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    r.raise_for_status()
    response = r.json().get('response', '')
    elapsed = time.time() - start
    print(f"Response ({elapsed:.1f}s):\n{response}\n")
    
    data = parse_json_response(response)
    if data:
        print(f"Parsed: {json.dumps(data, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

doc.close()
