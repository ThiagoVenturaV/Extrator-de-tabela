"""Test with llama3.2-vision:11b - more capable model."""
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
MODEL = "llama3.2-vision:11b"

pdf_path = 'input/Anexo (86992811).pdf'
doc = fitz.open(pdf_path)

# Test page 1 with different rotations using llama3.2-vision
for rotation in [0, 90]:
    page = doc[0]
    page.set_rotation(rotation)
    
    zoom = 200 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Also try PIL rotation for the 0-degree case
    if rotation == 0:
        # The text appears rotated 90° CW in the original, so rotate CCW
        img_rotated = img.rotate(90, expand=True)
    else:
        img_rotated = img
    
    buffer = io.BytesIO()
    img_rotated.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    img_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    # Save for inspection
    img_rotated.save(f'debug_pages/page_1_llama_rot{rotation}.png')
    
    print(f"\n--- Testing rotation={rotation} with {MODEL} ---")
    print(f"Image size: {img_rotated.size}")
    
    prompt = """Look at this scanned document image carefully. It is a "COMPROVANTE DE ENTREGA" (delivery receipt) from the Brazilian government.

There should be a table with columns like: Contrato nº, Descrição do material, Unidade, Quantidade, Tombamento.

Please extract ALL rows from the table in this JSON format:
{
  "tem_tabela": true,
  "destino": "school/destination name",
  "codigo_mec": "MEC code number",
  "linhas": [
    {"contrato": "contract number", "descricao": "material description", "quantidade": "quantity", "tombamento": "tombamento number"}
  ]
}

If there is truly no table, respond: {"tem_tabela": false}
Respond ONLY with JSON."""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4096}
    }
    
    start = time.time()
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=180)
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
