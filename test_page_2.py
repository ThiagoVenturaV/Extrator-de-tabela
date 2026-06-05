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
MODEL = "glm-ocr"

pdf_path = 'input/Anexo (86992811).pdf'
doc = fitz.open(pdf_path)

page = doc[1] # Page 2 (0-indexed 1)
zoom = 150 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# Rotate 90 degrees CCW
img_rotated = img.rotate(90, expand=True)

buffer = io.BytesIO()
img_rotated.save(buffer, format="JPEG", quality=80)
buffer.seek(0)
img_b64 = base64.b64encode(buffer.read()).decode('utf-8')

print(f"\n--- Testing page 2 (Signature Page) with {MODEL} ---")

payload = {
    "model": MODEL,
    "prompt": "Text Recognition:",
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
except Exception as e:
    print(f"Error: {e}")

doc.close()
