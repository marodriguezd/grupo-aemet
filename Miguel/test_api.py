import requests

url = "http://127.0.0.1:8000/historico/obtener_historico"
res = requests.get(url, params={"id": "3195", "fecha_inicio": "2020-01-01", "fecha_fin": "2020-01-31"})
print(res.status_code)
print(res.text)
