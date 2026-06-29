import json
from pathlib import Path

#Leer datos
with open("Carmen/limpieza json bucket 1/2026-06-22.json", encoding="utf-8") as f:
    datos = json.load(f)

print(type(datos))
print(len(datos))
print(datos[0])

# Mostrar todas las columnas presentes en el primer registro
print("\nColumnas:")
print(datos[0].keys())

# Número de columnas del primer registro
print("\nNúmero de columnas:", len(datos[0]))

# Comprobar si todos los registros tienen las mismas columnas
columnas = set()

for registro in datos:
    columnas.update(registro.keys())

print("\nTodas las columnas encontradas:")
print(sorted(columnas))
print("Total:", len(columnas))

#No todas las estaciones devuelven las mismas variables: 
#Por ahora tenemos 795 registros (estaciones), con 27 columnas en total. El primer registro solo tiene 19 columnas, lo que confirma que no todas las estaciones tienen todas las variables.

#¿cuantos valores faltan por columna?

from collections import Counter

faltantes = Counter()

for registro in datos:
    for columna in columnas:
        if columna not in registro or registro.get(columna) in (None, ""):
            faltantes[columna] += 1

print("\nValores faltantes por columna:")
for columna in sorted(columnas):
    print(f"{columna:15} -> {faltantes[columna]}")

#Algunas conclusiones por el camino:
#Variables muy completas que merece la pena conservar: fecha, indicativo, nombre, provincia, altitud, tmax, tmin, tmed, prec, hrMedia, hrMax, hrMin.
#variables completas que pueden ser interesantes para mantener: velmedia, racha, dir, horaracha.
#Variables con muchos huecos: presMax, presMin, horapresMax, horapresMin, sol, horaPIntMax.

#Columnas a conservar

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

# Función de limpieza

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
    

# Crear dataset limpio

datos_limpios = []

for registro in datos:

    nuevo_registro = {}

    for columna in columnas_utiles:
        nuevo_registro[columna] = convertir_valor(
            registro.get(columna)
        )

    datos_limpios.append(nuevo_registro)

#comprobar
print("\nPrimer registro limpio:\n")
print(datos_limpios[0])
print(type(datos_limpios[0]["altitud"]))
print(type(datos_limpios[0]["tmax"]))
print(type(datos_limpios[0]["prec"]))
print(type(datos_limpios[0]["nombre"]))
print(type(datos_limpios[0]["tmed"]))


# Guardar dataset limpio

with open(
    "Carmen/limpieza json bucket 1/datos_limpios.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(datos_limpios, f, ensure_ascii=False, indent=4)

print("\n JSON limpio guardado correctamente.")