import json

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