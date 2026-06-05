import fitz

pdf_path = 'input/Anexo (86992811).pdf'
doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}")
for i in range(min(10, len(doc))):
    page = doc[i]
    print(f"Page {i+1}: size={page.rect}, rotation={page.rotation}")

doc.close()
