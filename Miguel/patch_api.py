import json

with open("App_Interactiva.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and len(cell["source"]) > 0 and "%%writefile api_aemet.py\n" in cell["source"][0]:
        source = cell["source"]
        
        # Replace imports
        for i, line in enumerate(source):
            if line == "from datetime import date\n":
                source.insert(i+1, "import pickle\n")
                source.insert(i+2, "import os\n")
                source.insert(i+3, "import pandas as pd\n")
                source.insert(i+4, "import xgboost as xgb\n")
                break
                
        # Replace the functions
        new_source = []
        skip = False
        for line in source:
            if line.startswith("@app.post(\"/modelos_max/{idema}/predict\")"):
                skip = True
                
                new_funcs = [
                    "@app.post(\"/modelos_max/{idema}/predict\")\n",
                    "def prediccion_temp_max(idema: str, input_data: InputFeatures):\n",
                    "    \"\"\"Predicción real de temperatura máxima con XGBoost.\"\"\"\n",
                    "    idema_limpio = idema.strip().replace(\"/\", \"_\").replace(\"\\\\\", \"_\")\n",
                    "    ruta_modelo = f\"modelos_max/modelo_{idema_limpio}_max.pkl\"\n",
                    "    if not os.path.exists(ruta_modelo):\n",
                    "        raise HTTPException(status_code=404, detail=\"Modelo no entrenado para esta estación\")\n",
                    "    \n",
                    "    with open(ruta_modelo, \"rb\") as f:\n",
                    "        modelo = pickle.load(f)\n",
                    "        \n",
                    "    df_in = pd.DataFrame([{\"tmed\": input_data.features[0]}])\n",
                    "    valor_pred = float(modelo.predict(df_in)[0])\n",
                    "    \n",
                    "    return {\n",
                    "        \"status\": \"success\",\n",
                    "        \"idema\": idema,\n",
                    "        \"mensaje\": \"Predicción real (XGBoost)\",\n",
                    "        \"prediccion\": [[valor_pred]]\n",
                    "    }\n",
                    "\n",
                    "@app.post(\"/modelos_min/{idema}/predict\")\n",
                    "def prediccion_temp_min(idema: str, input_data: InputFeatures):\n",
                    "    \"\"\"Predicción real de temperatura mínima con XGBoost.\"\"\"\n",
                    "    idema_limpio = idema.strip().replace(\"/\", \"_\").replace(\"\\\\\", \"_\")\n",
                    "    ruta_modelo = f\"modelos_min/modelo_{idema_limpio}_min.pkl\"\n",
                    "    if not os.path.exists(ruta_modelo):\n",
                    "        raise HTTPException(status_code=404, detail=\"Modelo no entrenado para esta estación\")\n",
                    "    \n",
                    "    with open(ruta_modelo, \"rb\") as f:\n",
                    "        modelo = pickle.load(f)\n",
                    "        \n",
                    "    df_in = pd.DataFrame([{\"tmed\": input_data.features[0]}])\n",
                    "    valor_pred = float(modelo.predict(df_in)[0])\n",
                    "    \n",
                    "    return {\n",
                    "        \"status\": \"success\",\n",
                    "        \"idema\": idema,\n",
                    "        \"mensaje\": \"Predicción real (XGBoost)\",\n",
                    "        \"prediccion\": [[valor_pred]]\n",
                    "    }\n",
                    "\n"
                ]
                new_source.extend(new_funcs)
                continue
                
            if skip:
                if line.startswith("@app.get(\"/historico/obtener_historico\")"):
                    skip = False
                else:
                    continue
            
            if not skip:
                new_source.append(line)
                
        cell["source"] = new_source

with open("App_Interactiva.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
