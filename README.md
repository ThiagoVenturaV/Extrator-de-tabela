# Extrator e Consolidador de Tabelas PDF para Excel

Este projeto extrai tabelas de todas as páginas de arquivos PDF (mesmo com páginas rotacionadas digitalmente), consolida os dados em uma única tabela e exporta para uma planilha Excel (`.xlsx`) com colunas padronizadas.

As colunas finais geradas no Excel são:
1. **nome do documento** (nome do arquivo PDF de origem)
2. **contrato numero**
3. **destino**
4. **descricao do material**
5. **quantidade** (convertida em valor numérico quando possível)
6. **numero do mec**

---

## Estrutura do Projeto

```
pdf_table_extractor/
├── input/                  # Coloque seus arquivos PDF aqui
├── output/                 # O Excel resultante será salvo aqui
├── requirements.txt        # Dependências do Python (PyMuPDF, pandas, openpyxl)
├── extract_tables.py       # Script principal de extração
└── README.md               # Este arquivo de instruções
```

---

## Como Usar

### 1. Instalar Dependências
Abra o terminal (PowerShell ou Prompt de Comando) na pasta do projeto e instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Colocar os Arquivos PDF
Copie os arquivos PDF dos quais deseja extrair as tabelas e cole-os dentro da pasta `input/`. (Se a pasta `input` não existir ainda, ela será criada automaticamente ao rodar o script pela primeira vez).

### 3. Executar o Script
Rode o script no terminal:
```bash
python extract_tables.py
```

### 4. Verificar Resultados
O script lerá todos os PDFs presentes na pasta `input/` e gerará um arquivo consolidado chamado `tabela_consolidada.xlsx` dentro da pasta `output/`.

---

## Características Especiais

### Tratamento de Rotação de Páginas
O script utiliza a biblioteca `PyMuPDF` que possui suporte nativo para desrotacionar páginas temporariamente durante a busca por tabelas. Se o seu PDF possui páginas no formato paisagem (90°), invertidas (180°) ou qualquer outra rotação digital, o script lerá a tabela corretamente.

### Limpeza e Mapeamento de Colunas Flexível
O script busca termos semelhantes aos cabeçalhos desejados para fazer a correspondência de colunas de forma inteligente (ex: mapeia "Qtd", "Quantity", "Volume" para a coluna "quantidade"). Se necessário, você pode alterar ou adicionar sinônimos na variável `KEYWORDS` no início do script `extract_tables.py`.
