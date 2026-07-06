import psycopg
DSN = "postgresql://aemet2026:mondongo-dai07rt-aemet-2026@database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com:5432/postgres"
with psycopg.connect(DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'datos_climaticos';")
        print(cur.fetchall())
