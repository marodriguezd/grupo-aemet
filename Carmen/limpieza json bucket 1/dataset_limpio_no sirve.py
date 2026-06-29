import json
from pathlib import Path

ruta_json = Path(__file__).parent / "2026-06-22.json"

with open(ruta_json, encoding="utf-8") as f:
    datos = json.load(f)

    columnas_utiles = [
        "fecha",
        "indicativo",
        "nombre",
        "provincia",
        "altitud",
        "tmed",
        "tmin",
        "tmax",
        "prec",
        "dir",
        "velmedia",
        "racha",
        "hrMedia",
        "hrMax",
        "hrMin"
    ]

#convertir tipos

def convertir_valor(valor):
    if valor is None or valor == "":
        return None

    if not isinstance(valor, str):
        return valor

    valor = valor.strip()

    if "," in valor:
        valor = valor.replace(",", ".")

    try:
        if "." in valor:
            return float(valor)
        return int(valor)
    except ValueError:
        return valor
    
    #nuevo json 

datos_limpios = []

for registro in datos:
    nuevo = {}

    for columna in columnas_utiles:
        nuevo[columna] = convertir_valor(registro.get(columna))

    datos_limpios.append(nuevo)