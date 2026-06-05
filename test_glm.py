import sys
import time
import json
import base64
import io
import requests

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')
from extract_tables import *
from PIL import Image

OLLAMA_URL = "http://localhost:11434"
MODEL = "glm-ocr"

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
img_rotated.save('debug_pages/page_1_glm_rot90.png')

print(f"\n--- Testing page 1 with {MODEL} ---")
print(f"Image size: {img_rotated.size}")

prompt = "Text Recognition:"

payload = {
    "model": MODEL,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {"temperature": 0.1, "num_predict": 4096, "num_ctx": 16384}
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
