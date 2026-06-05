# Extrator e Consolidador de Tabelas PDF para Excel (Edição Ollama GLM-OCR)

Este projeto realiza a extração inteligente de tabelas de arquivos PDF complexos e/ou rotacionados, utilizando visão computacional e inteligência artificial local com o **Ollama**. Os dados extraídos são consolidados em uma única planilha Excel (`.xlsx`) padronizada.

O diferencial desta abordagem é o uso de modelos de visão locais, permitindo uma extração altamente robusta mesmo quando o layout do PDF varia, as tabelas não possuem marcações de texto selecionáveis ou as páginas estão rotacionadas digitalmente.

---

## 🚀 Como Funciona a Extração (Duas Etapas)

O script principal (`extract_tables.py`) processa cada página dos PDFs em duas etapas:

1. **Reconhecimento de Texto (Header/Metadados):**
   - A página do PDF é convertida em imagem e rotacionada 90° no sentido anti-horário (para ficar em pé).
   - Recorta-se o topo da imagem (40% da altura) para focar no cabeçalho do documento.
   - O Ollama (usando o prompt `Text Recognition:`) extrai informações-chave como: **Destino**, **Código MEC** e o **Número do Documento**.
   
2. **Reconhecimento da Tabela:**
   - O Ollama (usando o prompt `Table Recognition:`) analisa a imagem inteira da página para reconhecer a estrutura da tabela e retorná-la como um formato HTML limpo.
   - O script interpreta a tabela HTML gerada pelo modelo, limpa os valores de quantidade e mapeia os campos para colunas padronizadas.

---

## 📂 Estrutura do Projeto

```
pdf_table_extractor/
├── input/                  # Pasta para colocar os PDFs de origem
├── output/                 # Pasta onde o Excel gerado será salvo
├── requirements.txt        # Dependências do Python
├── extract_tables.py       # Script principal de extração de tabelas
├── inspect_pdf.py          # Script auxiliar para depuração e inspeção do PDF
├── parse_test.py           # Testes rápidos de parsing de HTML
├── test_*.py               # Scripts de testes com diferentes modelos (glm, qwen, etc.)
└── README.md               # Este arquivo com instruções
```

As colunas finais salvas na planilha são:
* `nome do documento` (nome do PDF de origem)
* `contrato numero`
* `destino`
* `codigo mec`
* `numero`
* `descricao do material`
* `quantidade` (convertida e limpa numericamente)
* `tombamento`

---

## 🛠️ Pré-requisitos

### 1. Instalar e rodar o Ollama
Para a extração visual, você precisará ter o **Ollama** instalado e rodando em sua máquina local.
- Baixe em: [ollama.com](https://ollama.com)
- Certifique-se de que o Ollama está rodando em segundo plano (`ollama serve`).

### 2. Instalar o Modelo de Visão
O script utiliza por padrão o modelo **`glm-ocr`**, que é muito rápido e leve. Instale-o com o comando:
```bash
ollama pull glm-ocr
```
*(Nota: Você também pode alterar a variável `VISION_MODEL` no script se quiser experimentar outros modelos como `qwen2.5-coder` ou `llama3`).*

### 3. Instalar Dependências do Python
Abra o terminal (PowerShell ou Prompt de Comando) na pasta do projeto e execute:
```bash
pip install -r requirements.txt
```

---

## 🏃 Como Usar

### 1. Colocar os Arquivos PDF
Coloque todos os seus PDFs de origem dentro da pasta `input/`. Se a pasta não existir, ela será criada automaticamente ao rodar o script.

### 2. Executar o Script

**Para processar todos os PDFs por completo:**
```bash
python extract_tables.py
```

**Para testar ou limitar a extração a um número máximo de páginas por PDF (útil para testes rápidos):**
```bash
# Limita o processamento a 3 páginas por arquivo
python extract_tables.py 3
```

### 3. Verificar os Resultados
- Durante o processamento, o script salva dados temporários em `output/tabela_parcial.xlsx` a cada 20 páginas, garantindo que você não perca o progresso caso o script seja interrompido.
- Ao final, o arquivo consolidado final estará disponível em: **`output/tabela_consolidada.xlsx`**.

---

## ⚙️ Configurações Adicionais

No arquivo `extract_tables.py`, você pode ajustar parâmetros como:
* `OLLAMA_URL`: URL da API do Ollama (padrão `http://localhost:11434`).
* `VISION_MODEL`: O modelo de OCR/visão utilizado (padrão `glm-ocr`).
* `DPI`: A resolução em que a página é renderizada em imagem (padrão `150`). Aumentar melhora o OCR em textos muito pequenos, mas consome mais memória e tempo.
