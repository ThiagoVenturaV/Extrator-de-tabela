import re

texts = [
    "nº 138.2025",
    "Nº 138.2025",
    "n.º 138.2025",
    "nº138.2025",
    "n.º138.2025",
    "numero 138.2025",
    "NÚMERO 138.2025",
    "nº 138-2025",
]

regex = r'(?:n\.\s*º|n[º°\.]|número|numero)\s*([\w\.\-]+)'

for t in texts:
    m = re.search(regex, t, re.IGNORECASE)
    val = m.group(1) if m else "NONE"
    print(f"Text: '{t}' -> Parsed: '{val}'")
