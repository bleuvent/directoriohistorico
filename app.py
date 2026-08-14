import sqlite3
import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Directorio Histórico de Establecimientos")

# Path a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "directorio.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/buscar/anio_rbd")
def buscar_anio_rbd(anio: str = Query(...), rbd: str = Query(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM historico 
        WHERE anio = ? AND rbd = ?
        ORDER BY anio DESC
        LIMIT 1000
    """, (anio, rbd))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

@app.get("/api/buscar/nombre")
def buscar_nombre(nombre: str = Query(...), limite: int = Query(1000)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM historico 
        WHERE nombre_establecimiento LIKE ? 
           OR nombre_antiguo LIKE ?
        ORDER BY nombre_establecimiento
        LIMIT ?
    """, (f"%{nombre}%", f"%{nombre}%", limite))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

@app.get("/api/progreso")
def progreso():
    conn = get_db()
    cursor = conn.cursor()

    # Total nacional
    cursor.execute("SELECT COUNT(*) FROM historico WHERE anio IS NOT NULL AND anio != ''")
    total_nacional = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM historico WHERE est_digit = 'ONLINE'")
    online_nacional = cursor.fetchone()[0]

    # RM (region 13)
    cursor.execute("SELECT COUNT(*) FROM historico WHERE region = '13' AND anio IS NOT NULL AND anio != ''")
    total_rm = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM historico WHERE region = '13' AND est_digit = 'ONLINE'")
    online_rm = cursor.fetchone()[0]

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
    cursor.execute("""
        SELECT * FROM historico WHERE rbd = ? ORDER BY anio DESC
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
