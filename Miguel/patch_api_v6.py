import json

with open("App_Interactiva.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] != "code" or not cell["source"]: continue
    
    if "%%writefile api_aemet.py\n" in cell["source"][0] or "%%writefile api_aemet.py" in cell["source"][0]:
        source = cell["source"]
        for i, line in enumerate(source):
            if 'return {"fecha": str(fila[0]), "tmed": float(fila[1])}' in line:
                source[i] = line.replace(
                    'return {"fecha": str(fila[0]), "tmed": float(fila[1])}',
                    'return {"fecha": str(fila[0]), "tmed": float(fila[1]), "nombre": str(fila[2])}'
                )
        cell["source"] = source

with open("App_Interactiva.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
