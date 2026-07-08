import json

with open("App_Interactiva.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] != "code" or not cell["source"]: continue
    
    if "%%writefile web_aemet.py\n" in cell["source"][0] or "%%writefile web_aemet.py" in cell["source"][0]:
        source = cell["source"]
        
        for i, line in enumerate(source):
            if "st.success(f\"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult})\")" in line:
                # Reemplazamos la linea para añadir el IDEMA
                source[i] = line.replace(
                    "st.success(f\"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult})\")",
                    "st.success(f\"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult}) — IDEMA: {idema}\")"
                )
                break
                
        cell["source"] = source

with open("App_Interactiva.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
