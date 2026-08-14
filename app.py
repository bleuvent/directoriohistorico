import sqlite3
import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="Directorio Histórico de Establecimientos")

DB_PATH = os.path.join(os.path.dirname(__file__), "directorio.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_column_name(table, candidates):
    """Encuentra el nombre real de una columna sin importar mayúsculas."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table}");')
    cols = [c[1] for c in cursor.fetchall()]
    conn.close()
    for c in cols:
        if c.lower() in [x.lower() for x in candidates]:
            return c
    return None

# Detectar nombres de columnas al iniciar
COL_ANIO = get_column_name("historico", ["anio", "año", "ano", "agno"])
COL_RBD = get_column_name("historico", ["rbd"])
COL_TOMO = get_column_name("historico", ["tomo", "TOMO", "Tomo", "caja_tomo"])
COL_REGION = get_column_name("historico", ["region", "REGION", "Region"])
COL_NOMBRE = get_column_name("historico", ["nombre_establecimiento", "nombre", "nombre_de_establecimiento"])
COL_NOMBRE_ANT = get_column_name("historico", ["nombre_antiguo", "NOMBRE_ANTIGUO"])
COL_COMUNA = get_column_name("historico", ["comuna", "COMUNA"])

print(f"📊 Columnas detectadas: anio={COL_ANIO}, rbd={COL_RBD}, tomo={COL_TOMO}, region={COL_REGION}")

# Helper para escapar nombres de columnas en SQL
def q(col):
    return f'"{col}"' if col else '"columna"'

@app.get("/api/buscar/anio_rbd")
def buscar_anio_rbd(anio: str = Query(...), rbd: str = Query(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM historico
        WHERE {q(COL_ANIO)} = ? AND {q(COL_RBD)} = ?
        ORDER BY {q(COL_ANIO)} DESC
        LIMIT 1000
    """, (anio, rbd))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

@app.get("/api/buscar/nombre")
def buscar_nombre(nombre: str = Query(...), limite: int = Query(1000)):
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if COL_NOMBRE:
        conditions.append(f"{q(COL_NOMBRE)} LIKE ?")
        params.append(f"%{nombre}%")
    if COL_NOMBRE_ANT:
        conditions.append(f"{q(COL_NOMBRE_ANT)} LIKE ?")
        params.append(f"%{nombre}%")

    if not conditions:
        conn.close()
        return {"resultados": [], "total": 0}

    where_clause = " OR ".join(conditions)
    order_by = f"ORDER BY {q(COL_NOMBRE)}" if COL_NOMBRE else ""

    cursor.execute(f"""
        SELECT * FROM historico
        WHERE {where_clause}
        {order_by}
        LIMIT ?
    """, (*params, limite))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

@app.get("/api/progreso")
def progreso():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM historico")
    total_nacional = cursor.fetchone()[0]

    if COL_TOMO:
        cursor.execute(f'SELECT COUNT(*) FROM historico WHERE {q(COL_TOMO)} IS NOT NULL AND {q(COL_TOMO)} != ''')
        online_nacional = cursor.fetchone()[0]
    else:
        online_nacional = 0

    if COL_REGION:
        cursor.execute(f'SELECT COUNT(*) FROM historico WHERE {q(COL_REGION)} = '13'')
        total_rm = cursor.fetchone()[0]

        if COL_TOMO:
            cursor.execute(f'SELECT COUNT(*) FROM historico WHERE {q(COL_REGION)} = '13' AND {q(COL_TOMO)} IS NOT NULL AND {q(COL_TOMO)} != ''')
            online_rm = cursor.fetchone()[0]
        else:
            online_rm = 0
    else:
        total_rm = 0
        online_rm = 0

    conn.close()

    return {
        "nacional": {
            "total": total_nacional,
            "online": online_nacional,
            "porcentaje": round(online_nacional / total_nacional * 100, 2) if total_nacional > 0 else 0
        },
        "rm": {
            "total": total_rm,
            "online": online_rm,
            "porcentaje": round(online_rm / total_rm * 100, 2) if total_rm > 0 else 0
        }
    }

@app.get("/api/ubicacion/{codigo}")
def get_ubicacion(codigo: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ubicaciones WHERE codigo = ?", (codigo,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"error": "Ubicación no encontrada"}

@app.get("/api/online/{anio}/{rbd}")
def get_online(anio: str, rbd: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM online
        WHERE anio = ? AND rbd = ?
        ORDER BY curso, letra
    """, (anio, rbd))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

@app.get("/api/establecimiento/{rbd}")
def get_establecimiento(rbd: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM historico WHERE {q(COL_RBD)} = ? ORDER BY {q(COL_ANIO)} DESC
    """, (rbd,))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
