import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://carmencortesbrezmes@localhost:5432/aemet"
)

archivos = [
    f"Miguel/sheets/csv/climaticos_{anio}.csv"
    for anio in range(2016, 2027)
]

primero = True

for archivo in archivos:

    print(f"Leyendo {archivo}...")

    df = pd.read_csv(archivo)

    print(f"Filas: {len(df):,}")

    df.to_sql(
        "clima",
        engine,
        if_exists="replace" if primero else "append",
        index=False
    )

    primero = False

    print("Cargado correctamente\n")

print("Carga completa terminada")