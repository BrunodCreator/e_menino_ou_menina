import os
from dotenv import dotenv_values
import psycopg2

DATABASE_URL ="postgresql://postgres:cVHGlRoseeNNNiJUKqivXnGhpMMldVpq@ballast.proxy.rlwy.net:49048/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print("Conexão bem-sucedida! Versão do PostgreSQL:", version)
    cursor.close()
    conn.close()
except Exception as e:
    print("Erro ao conectar ao banco de dados:", e)