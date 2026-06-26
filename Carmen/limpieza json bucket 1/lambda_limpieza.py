import json
import boto3

s3 = boto3.client("s3")

def convertir_valor(valor):

    if valor is None or valor == "":
        return None

    if not isinstance(valor, str):
        return valor

    valor = valor.strip()
    valor = valor.replace(",", ".")

    try:
        if "." in valor:
            return float(valor)
        return int(valor)

    except ValueError:
        return valor
    
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

def limpiar_datos(datos):

    datos_limpios = []

    for registro in datos:

        nuevo_registro = {}

        for columna in columnas_utiles:
            nuevo_registro[columna] = convertir_valor(
                registro.get(columna)
            )

        datos_limpios.append(nuevo_registro)

    return datos_limpios

