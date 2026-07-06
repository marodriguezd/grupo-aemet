
import pandas as pd
from fastapi import FastAPI , HTTPException ,   Request, HTTPException
from temperatura_minima import router_temp_min
from temperatura_maxima import router_temp_max
from historico import router_historico
import os
from contextlib import asynccontextmanager
import pickle

# en la terminal ingresar el siguiente codigo 

# uvicorn AEMET:app --reload

# en el buscador de google ingresar 

# http://127.0.0.1:8000/docs


app = FastAPI( title = "AEMET", description = "fastapi AEMET.", version = "0.0.1")


@app.get("/")
def bienvenida():
    return{"mensaje": "Bienvenido a la API de AEMET, para ver la documentacion de la API ingrese a /docs"}






app.include_router(router = router_temp_max)         
app.include_router(router = router_temp_min)     
app.include_router(router = router_historico)

