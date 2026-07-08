import json

with open("App_Interactiva.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] != "code" or not cell["source"]: continue
    
    # 1. API endpoint modification
    if "%%writefile api_aemet.py\n" in cell["source"][0]:
        source = cell["source"]
        
        # Check if already added
        if any("ultima_tmed" in line for line in source):
            continue
            
        # Find where to insert (before @app.get("/historico/obtener_historico"))
        insert_idx = -1
        for i, line in enumerate(source):
            if line.startswith("@app.get(\"/historico/obtener_historico\")"):
                insert_idx = i
                break
                
        if insert_idx != -1:
            new_endpoint = [
                "@app.get(\"/historico/ultima_tmed\")\n",
                "def ultima_tmed(idema: str = Query(..., alias=\"id\")):\n",
                "    \"\"\"Consulta la última tmed registrada para una estación.\"\"\"\n",
                "    try:\n",
                "        with psycopg.connect(DSN) as conn:\n",
                "            with conn.cursor() as cur:\n",
                "                query = \"\"\"\n",
                "                    SELECT fecha, tmed \n",
                "                    FROM datos_climaticos \n",
                "                    WHERE indicativo = %s AND tmed IS NOT NULL\n",
                "                    ORDER BY fecha DESC\n",
                "                    LIMIT 1;\n",
                "                \"\"\"\n",
                "                cur.execute(query, (idema,))\n",
                "                fila = cur.fetchone()\n",
                "                \n",
                "        if fila:\n",
                "            return {\"fecha\": str(fila[0]), \"tmed\": float(fila[1])}\n",
                "        else:\n",
                "            raise HTTPException(status_code=404, detail=\"No hay datos de tmed para esta estación\")\n",
                "    except HTTPException:\n",
                "        raise\n",
                "    except Exception as e:\n",
                "        print(f\"Error en BD: {e}\")\n",
                "        raise HTTPException(status_code=500, detail=\"Error al conectar a la BD\")\n",
                "\n"
            ]
            for line in reversed(new_endpoint):
                source.insert(insert_idx, line)
                
    # 2. Web UI modification
    if "%%writefile web_aemet.py\n" in cell["source"][0]:
        source = cell["source"]
        
        start_idx = -1
        end_idx = -1
        for i, line in enumerate(source):
            if line.startswith("    idema = st.text_input(\"Código de la estación (IDEMA):\""):
                start_idx = i
            elif line.startswith("elif opcion == \"Histórico\":\n") and start_idx != -1:
                end_idx = i
                break
                
        if start_idx != -1 and end_idx != -1:
            new_web_logic = [
                "    idema = st.text_input(\"Código de la estación (IDEMA):\", value=\"0009X\")\n",
                "    \n",
                "    modo_prediccion = st.radio(\"Método de entrada:\", [\"Entrada Manual\", \"Usar última temperatura registrada\"])\n",
                "    \n",
                "    if modo_prediccion == \"Entrada Manual\":\n",
                "        valor = st.number_input(\"Valor numérico de entrada (ej. temperatura actual):\", value=15.0)\n",
                "    else:\n",
                "        st.info(\"Se buscará automáticamente la última temperatura media de esta estación en la base de datos.\")\n",
                "        valor = None\n",
                "    \n",
                "    if st.button(\"Calcular\"):\n",
                "        with st.spinner(\"Conectando con la API...\"):\n",
                "            if modo_prediccion == \"Usar última temperatura registrada\":\n",
                "                url_ultima = f\"{FASTAPI_URL}/historico/ultima_tmed\"\n",
                "                try:\n",
                "                    res_ult = realizar_peticion('GET', url_ultima, params={\"id\": idema})\n",
                "                    data_ult = res_ult.json()\n",
                "                    valor = data_ult[\"tmed\"]\n",
                "                    fecha_ult = data_ult[\"fecha\"]\n",
                "                    st.success(f\"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult})\")\n",
                "                except requests.exceptions.HTTPError as e:\n",
                "                    st.error(f\"Error al obtener última temperatura: {e}\")\n",
                "                    st.stop()\n",
                "                except Exception as e:\n",
                "                    st.error(f\"Error de conexión: {e}\")\n",
                "                    st.stop()\n",
                "                    \n",
                "            ruta = \"modelos_max\" if opcion == \"Temperatura Máxima\" else \"modelos_min\"\n",
                "            url = f\"{FASTAPI_URL}/{ruta}/{idema}/predict\"\n",
                "            \n",
                "            try:\n",
                "                res = realizar_peticion('POST', url, json={\"features\": [valor]})\n",
                "                data = res.json()\n",
                "                st.success(data[\"mensaje\"])\n",
                "                \n",
                "                valor_pred = data[\"prediccion\"][0][0]\n",
                "                st.metric(label=f\"Predicción ({idema})\", value=f\"{valor_pred:.2f} °C\")\n",
                "            except requests.exceptions.HTTPError as e:\n",
                "                st.error(f\"La API devolvió un error de servidor: {e}\")\n",
                "            except requests.exceptions.RequestException as e:\n",
                "                st.error(f\"Hubo un error al conectar con la API tras varios reintentos: {e}\")\n",
                "\n"
            ]
            del source[start_idx:end_idx]
            for line in reversed(new_web_logic):
                source.insert(start_idx, line)

with open("App_Interactiva.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
