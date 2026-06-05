import os
import sys
import functools

# Reconfigure stdout/stderr to UTF-8 to prevent encoding crashes on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Force all prints to flush immediately to avoid buffering issues on Windows
print = functools.partial(print, flush=True)

import glob
import re
import json
import base64
import io
import time
import fitz  # PyMuPDF
import pandas as pd
import requests
from PIL import Image

# --- Configuration ---
OLLAMA_URL = "http://localhost:11434"
VISION_MODEL = "glm-ocr"  # Extremely fast and light OCR model (0.9B)
DPI = 150  # 150 DPI is standard and fast
MAX_RETRIES = 2

# Target columns for the final Excel file
TARGET_COLUMNS = [
    'nome do documento',
    'contrato numero',
    'destino',
    'codigo mec',
    'numero',
    'descricao do material',
    'quantidade',
    'tombamento'
]

def pdf_page_to_pil(page, dpi=DPI):
    """Convert a PyMuPDF page to a PIL image, rotated 90 degrees CCW to be upright."""
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img.rotate(90, expand=True)


def pil_to_base64(img, quality=80):
    """Convert a PIL image to a base64 encoded JPEG string."""
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def check_ollama():
    """Check if Ollama is running and the model is available."""
    global VISION_MODEL
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m['name'] for m in r.json().get('models', [])]
        print(f"[INFO] Ollama conectado. Modelos: {', '.join(models)}")

        if VISION_MODEL not in models:
            matching = [m for m in models if VISION_MODEL in m]
            if matching:
                VISION_MODEL = matching[0]
                print(f"[INFO] Usando modelo: {VISION_MODEL}")
            else:
                print(f"[ERRO] Modelo {VISION_MODEL} não encontrado.")
                print(f"Instale com: ollama pull {VISION_MODEL}")
                return False
        return True
    except requests.exceptions.ConnectionError:
        print("[ERRO] Ollama não está rodando. Inicie com: ollama serve")
        return False
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao Ollama: {e}")
        return False


def query_vision_model(image_base64, prompt, retries=MAX_RETRIES):
    """Send an image to the Ollama vision model and get the response."""
    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
            "num_ctx": 16384  # Crucial context window parameter for glm-ocr
        }
    }

    for attempt in range(retries + 1):
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=120
            )
            r.raise_for_status()
            return r.json().get('response', '')
        except requests.exceptions.Timeout:
            if attempt < retries:
                print(f"      Timeout, tentativa {attempt + 2}/{retries + 1}...")
                time.sleep(2)
            else:
                print(f"      [ERRO] Timeout após {retries + 1} tentativas")
                return None
        except Exception as e:
            if attempt < retries:
                print(f"      Erro: {e}, tentativa {attempt + 2}/{retries + 1}...")
                time.sleep(2)
            else:
                print(f"      [ERRO] Falha após {retries + 1} tentativas: {e}")
                return None


def clean_quantity(val):
    """Cleans quantity field."""
    if not val:
        return ""
    val_str = str(val).strip()
    if not val_str:
        return ""
    val_str = re.sub(r'[^\d.,-]', '', val_str)

    if ',' in val_str and '.' not in val_str:
        parts = val_str.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            val_str = val_str.replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    elif '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')

    try:
        num = float(val_str)
        if num.is_integer():
            return int(num)
        return num
    except ValueError:
        return val_str


def parse_html_table(html_table):
    """Parse table headers and rows from HTML string returned by Table Recognition."""
    rows_data = []
    
    # Extract headers from thead
    thead_match = re.search(r'<thead>(.*?)</thead>', html_table, re.DOTALL | re.IGNORECASE)
    headers = []
    if thead_match:
        headers = [re.sub(r'<.*?>', '', th).strip().lower() for th in re.findall(r'<th>(.*?)</th>', thead_match.group(1), re.DOTALL | re.IGNORECASE)]
    
    # Extract body rows
    tbody_match = re.search(r'<tbody>(.*?)</tbody>', html_table, re.DOTALL | re.IGNORECASE)
    if not tbody_match:
        # Fallback to general tr search if no tbody
        trs = re.findall(r'<tr>(.*?)</tr>', html_table, re.DOTALL | re.IGNORECASE)
    else:
        trs = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL | re.IGNORECASE)
        
    for tr in trs:
        tds = [re.sub(r'<.*?>', '', td).strip() for td in re.findall(r'<td>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)]
        if not tds:
            continue
            
        row_data = {
            'contrato': '',
            'descricao': '',
            'quantidade': '',
            'tombamento': ''
        }
        
        # Map values dynamically based on header names
        for idx, val in enumerate(tds):
            if idx < len(headers):
                header = headers[idx]
                if 'contrato' in header:
                    row_data['contrato'] = val
                elif 'descri' in header:
                    row_data['descricao'] = val
                elif 'quant' in header:
                    row_data['quantidade'] = val
                elif 'tomb' in header:
                    row_data['tombamento'] = val
            else:
                # Fallback to default index mapping
                if idx == 0:
                    row_data['contrato'] = val
                elif idx == 1:
                    row_data['descricao'] = val
                elif idx == 3:
                    row_data['quantidade'] = val
                elif idx == 4:
                    row_data['tombamento'] = val
                    
        rows_data.append(row_data)
        
    return rows_data


def extract_tables_from_pdf(pdf_path, max_pages=None):
    """Extracts tables from a PDF using glm-ocr model with a two-step method."""
    doc_name = os.path.basename(pdf_path)
    print(f"\n[INFO] Lendo arquivo: {doc_name}")

    doc = fitz.open(pdf_path)
    all_rows = []
    pages_with_tables = 0
    pages_without = 0

    # Stateful variables to propagate school/header info to continuation pages
    current_destino = ""
    current_codigo_mec = ""
    current_numero = ""

    total_pages = len(doc)
    limit_pages = min(total_pages, max_pages) if max_pages is not None else total_pages
    print(f"[INFO] Total de páginas a processar: {limit_pages} (de {total_pages})")
    print(f"[INFO] Tempo estimado: ~{limit_pages * 8 / 60:.1f} minutos")
    print()

    for page_num in range(limit_pages):
        page = doc[page_num]
        progress = f"  [{page_num + 1}/{limit_pages}]"

        # Convert page to upright PIL image
        img = pdf_page_to_pil(page)

        # Crop top 40% height of page for Text Recognition (focuses on header and school destination)
        width, height = img.size
        img_cropped = img.crop((0, 0, width, int(height * 0.40)))
        img_text_b64 = pil_to_base64(img_cropped)

        # Step 1: Text Recognition to identify if page has a table and extract headers
        start_time = time.time()
        text_response = query_vision_model(img_text_b64, "Text Recognition:")
        elapsed_text = time.time() - start_time

        if not text_response:
            print(f"{progress} Sem resposta no Text Recognition ({elapsed_text:.1f}s)")
            pages_without += 1
            continue

        # Check if the page is a table/receipt page (usually has 'destino', 'código mec', or 'contrato')
        text_lower = text_response.lower()
        if 'destino' not in text_lower and 'contrato' not in text_lower and 'comprovante de entrega' not in text_lower:
            print(f"{progress} Sem tabela ({elapsed_text:.1f}s)")
            pages_without += 1
            continue

        # Parse Destino and MEC from Text Recognition
        destino_match = re.search(r'Destino:\s*(.*?)\s*\n(?=\w+:|\w+\s+\w+:)', text_response, re.DOTALL | re.IGNORECASE)
        destino = destino_match.group(1).replace('\n', ' ').strip() if destino_match else ""
        if not destino:
            # Fallback regex in case formatting differs
            destino_match = re.search(r'Destino:\s*(.*?)\s*\n', text_response, re.IGNORECASE)
            destino = destino_match.group(1).strip() if destino_match else ""

        mec_match = re.search(r'Código MEC:\s*(\d+)', text_response, re.IGNORECASE)
        codigo_mec = mec_match.group(1).strip() if mec_match else ""

        # Parse Numero from Text Recognition (e.g. nº 138.2025), filtering out false matches
        numero_matches = re.finditer(r'(?:n\.\s*º|n[º°\.]|número|numero)\s*([\w\.\-]+)', text_response, re.IGNORECASE)
        numero = ""
        for m in numero_matches:
            match_val = m.group(1).strip().rstrip('.,-')
            if not any(c.isdigit() for c in match_val):
                continue
            if match_val.lower() in ['descrição', 'descricao', 'contrato', 'unidade', 'quantidade', 'tombamento']:
                continue
            
            # Skip if preceded by "contrato" (e.g. contract number)
            start_idx = m.start()
            preceding_text = text_response[max(0, start_idx-20):start_idx].lower()
            if 'contrato' in preceding_text:
                continue
                
            numero = match_val
            break

        # Update persistent values if new ones are found on this page
        if destino:
            current_destino = destino
        if codigo_mec:
            current_codigo_mec = codigo_mec
        if numero:
            current_numero = numero

        # Step 2: Table Recognition to extract clean HTML table rows
        start_time_table = time.time()
        img_table_b64 = pil_to_base64(img)
        table_response = query_vision_model(img_table_b64, "Table Recognition:")
        elapsed_table = time.time() - start_time_table
        total_elapsed = elapsed_text + elapsed_table

        if not table_response or 'table' not in table_response.lower():
            print(f"{progress} Falha ao extrair tabela ({total_elapsed:.1f}s)")
            pages_without += 1
            continue

        # Parse the HTML table
        linhas = parse_html_table(table_response)

        if not linhas:
            print(f"{progress} Tabela vazia ou formato inválido ({total_elapsed:.1f}s)")
            pages_without += 1
            continue

        pages_with_tables += 1
        print(f"{progress} [OK] {len(linhas)} linha(s) | Destino: {current_destino[:50]}... ({total_elapsed:.1f}s)")

        for linha in linhas:
            row_data = {col: "" for col in TARGET_COLUMNS}
            row_data['nome do documento'] = doc_name
            row_data['contrato numero'] = str(linha.get('contrato', '')).strip()
            row_data['destino'] = current_destino
            row_data['codigo mec'] = current_codigo_mec
            row_data['numero'] = current_numero
            row_data['descricao do material'] = str(linha.get('descricao', '')).strip()
            row_data['quantidade'] = clean_quantity(linha.get('quantidade', ''))
            row_data['tombamento'] = str(linha.get('tombamento', '')).strip()

            # Add if at least one field has data
            if any(v for k, v in row_data.items() if k != 'nome do documento' and str(v).strip()):
                all_rows.append(row_data)

        # Periodic save every 20 pages with tables
        if pages_with_tables > 0 and pages_with_tables % 20 == 0:
            _save_partial(all_rows, doc_name)

    doc.close()
    print(f"\n  Resumo: {pages_with_tables} página(s) com tabela, {pages_without} sem tabela")
    return all_rows


def _save_partial(all_rows, doc_name):
    """Save partial results in case of interruption."""
    if not all_rows:
        return
    try:
        df = pd.DataFrame(all_rows)
        df = df[TARGET_COLUMNS]
        partial_path = os.path.join('output', 'tabela_parcial.xlsx')
        df.to_excel(partial_path, index=False)
        print(f"    [SAVE] Salvo parcial: {len(df)} linhas")
    except Exception as e:
        print(f"    [SAVE ERR] Falha ao salvar parcial: {e}")


def main():
    input_dir = 'input'
    output_dir = 'output'
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  PDF Table Extractor - Ollama GLM-OCR Edition")
    print("=" * 60)
    print(f"Pasta de entrada: {os.path.abspath(input_dir)}")
    print(f"Pasta de saída:   {os.path.abspath(output_dir)}")
    print(f"Modelo:           {VISION_MODEL}")
    print(f"Resolução:        {DPI} DPI")
    print()

    if not check_ollama():
        sys.exit(1)

    max_pages = None
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
            print(f"[INFO] Limitando a extração a no máximo {max_pages} página(s) por arquivo.")
        except ValueError:
            pass

    pdf_files = glob.glob(os.path.join(input_dir, '*.pdf'))

    if not pdf_files:
        print("\n[INFO] Nenhum arquivo PDF encontrado na pasta 'input'.")
        return

    print(f"\nEncontrado(s) {len(pdf_files)} arquivo(s) PDF para processar.")

    all_data = []
    total_start = time.time()

    for pdf_path in pdf_files:
        try:
            rows = extract_tables_from_pdf(pdf_path, max_pages=max_pages)
            all_data.extend(rows)
            print(f"\n[OK] Extraído {len(rows)} linhas de {os.path.basename(pdf_path)}")
        except Exception as e:
            print(f"[ERRO] Falha ao processar {os.path.basename(pdf_path)}: {e}")
            import traceback
            traceback.print_exc()

    total_elapsed = time.time() - total_start

    if not all_data:
        print("\n[AVISO] Nenhuma tabela foi extraída com sucesso dos PDFs.")
        return

    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df[TARGET_COLUMNS]
    df = df.dropna(subset=[col for col in TARGET_COLUMNS if col != 'nome do documento'], how='all')

    # Export to Excel
    output_path = os.path.join(output_dir, 'tabela_consolidada.xlsx')
    try:
        df.to_excel(output_path, index=False)
        print(f"\n{'=' * 60}")
        print(f"  SUCESSO!")
        print(f"{'=' * 60}")
        print(f"Arquivo:     {os.path.abspath(output_path)}")
        print(f"Linhas:      {len(df)}")
        print(f"Tempo total: {total_elapsed/60:.1f} minutos")

        print(f"\nPrévia (primeiras 15 linhas):")
        print("-" * 60)
        preview_cols = ['contrato numero', 'descricao do material', 'quantidade', 'tombamento']
        print(df[preview_cols].head(15).to_string(index=False))
    except Exception as e:
        print(f"\n[ERRO] Falha ao salvar arquivo Excel: {e}")

    # Clean up partial file
    partial_path = os.path.join(output_dir, 'tabela_parcial.xlsx')
    if os.path.exists(partial_path):
        try:
            os.remove(partial_path)
        except Exception as e:
            print(f"    [INFO] Não foi possível remover o arquivo temporário {partial_path}: {e}")


if __name__ == '__main__':
    main()
