import sqlite3
import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import uvicorn

app = FastAPI(title="Directorio Historico de Establecimientos")

DB_PATH = os.path.join(os.path.dirname(__file__), "directorio.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_column_name(table, candidates):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info("' + table + '");')
    cols = [c[1] for c in cursor.fetchall()]
    conn.close()
    for c in cols:
        if c.lower() in [x.lower() for x in candidates]:
            return c
    return None

COL_ANIO = get_column_name("historico", ["anio", "ano", "agno"])
COL_RBD = get_column_name("historico", ["rbd"])
COL_TOMO = get_column_name("historico", ["tomo", "TOMO", "Tomo", "caja_tomo"])
COL_REGION = get_column_name("historico", ["region", "REGION", "Region"])
COL_NOMBRE = get_column_name("historico", ["nombre_establecimiento", "nombre", "nombre_de_establecimiento"])
COL_NOMBRE_ANT = get_column_name("historico", ["nombre_antiguo", "NOMBRE_ANTIGUO"])
COL_COMUNA = get_column_name("historico", ["comuna", "COMUNA"])
COL_OBSERVACIONES_HIST = get_column_name("historico", ["observacion", "observación", "observaciones", "OBSERVACION", "OBSERVACIÓN", "OBSERVACIONES", "obs"])
COL_OBSERVACIONES_ONLINE = get_column_name("online", ["observacion", "observación", "observaciones", "OBSERVACION", "OBSERVACIÓN", "OBSERVACIONES", "obs", "observaciones_acta"])

# NUEVO: Detectar columna de URL automáticamente
COL_URL = get_column_name("online", [
    "url_sharepoint", "enlace", "link", "url", "URL", 
    "Enlace", "LINK", "sharepoint", "SHAREPOINT"
])

print("Columnas historico: anio=" + str(COL_ANIO) + ", rbd=" + str(COL_RBD) + ", tomo=" + str(COL_TOMO) + ", obs=" + str(COL_OBSERVACIONES_HIST))
print("Columnas online: obs=" + str(COL_OBSERVACIONES_ONLINE) + ", url=" + str(COL_URL))

def q(col):
    return '"' + col + '"' if col else '"columna"'

@app.get("/api/buscar/anio_rbd")
def buscar_anio_rbd(anio: str = Query(...), rbd: str = Query(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico WHERE " + q(COL_ANIO) + " = ? AND " + q(COL_RBD) + " = ? ORDER BY " + q(COL_ANIO) + " DESC LIMIT 1000", (anio, rbd))
    rows = cursor.fetchall()
    conn.close()
    
    resultados = []
    for row in rows:
        d = dict(row)
        if COL_OBSERVACIONES_HIST and COL_OBSERVACIONES_HIST in d:
            d["observaciones"] = d[COL_OBSERVACIONES_HIST]
        resultados.append(d)
        
    return {"resultados": resultados, "total": len(resultados)}

@app.get("/api/buscar/nombre")
def buscar_nombre(nombre: str = Query(...), limite: int = Query(1000), region: Optional[str] = Query(None), comuna: Optional[str] = Query(None), anio: Optional[str] = Query(None)):
    conn = get_db()
    cursor = conn.cursor()
    conditions = []
    params = []
    if COL_NOMBRE:
        conditions.append(q(COL_NOMBRE) + " LIKE ?")
        params.append("%" + nombre + "%")
    if COL_NOMBRE_ANT:
        conditions.append(q(COL_NOMBRE_ANT) + " LIKE ?")
        params.append("%" + nombre + "%")
    if not conditions:
        conn.close()
        return {"resultados": [], "total": 0}
    where_clause = " OR ".join(conditions)
    if region and COL_REGION:
        where_clause = "(" + where_clause + ") AND " + q(COL_REGION) + " = ?"
        params.append(region)
    if comuna and COL_COMUNA:
        where_clause = "(" + where_clause + ") AND " + q(COL_COMUNA) + " = ?"
        params.append(comuna)
    if anio and COL_ANIO:
        where_clause = "(" + where_clause + ") AND " + q(COL_ANIO) + " = ?"
        params.append(anio)
    order_by = "ORDER BY " + q(COL_NOMBRE) if COL_NOMBRE else ""
    cursor.execute("SELECT * FROM historico WHERE " + where_clause + " " + order_by + " LIMIT ?", (*params, limite))
    rows = cursor.fetchall()
    conn.close()

    resultados = []
    for row in rows:
        d = dict(row)
        if COL_OBSERVACIONES_HIST and COL_OBSERVACIONES_HIST in d:
            d["observaciones"] = d[COL_OBSERVACIONES_HIST]
        resultados.append(d)

    return {"resultados": resultados, "total": len(resultados)}

@app.get("/api/filtros/valores")
def filtros_valores():
    conn = get_db()
    cursor = conn.cursor()
    result = {"regiones": [], "comunas": [], "anios": []}
    if COL_REGION:
        cursor.execute("SELECT DISTINCT " + q(COL_REGION) + " FROM historico WHERE " + q(COL_REGION) + " IS NOT NULL AND " + q(COL_REGION) + " != '' ORDER BY " + q(COL_REGION))
        result["regiones"] = [r[0] for r in cursor.fetchall()]
    if COL_COMUNA:
        cursor.execute("SELECT DISTINCT " + q(COL_COMUNA) + " FROM historico WHERE " + q(COL_COMUNA) + " IS NOT NULL AND " + q(COL_COMUNA) + " != '' ORDER BY " + q(COL_COMUNA))
        result["comunas"] = [r[0] for r in cursor.fetchall()]
    if COL_ANIO:
        cursor.execute("SELECT DISTINCT " + q(COL_ANIO) + " FROM historico WHERE " + q(COL_ANIO) + " IS NOT NULL AND " + q(COL_ANIO) + " != '' ORDER BY " + q(COL_ANIO) + " DESC")
        result["anios"] = [r[0] for r in cursor.fetchall()]
    conn.close()
    return result

@app.get("/api/progreso")
def progreso():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM historico")
    total_nacional = cursor.fetchone()[0]
    if COL_TOMO:
        cursor.execute("SELECT COUNT(*) FROM historico WHERE " + q(COL_TOMO) + " IS NOT NULL AND " + q(COL_TOMO) + " != ''")
        online_nacional = cursor.fetchone()[0]
    else:
        online_nacional = 0
    if COL_REGION:
        cursor.execute("SELECT COUNT(*) FROM historico WHERE " + q(COL_REGION) + " = '13'")
        total_rm = cursor.fetchone()[0]
        if COL_TOMO:
            cursor.execute("SELECT COUNT(*) FROM historico WHERE " + q(COL_REGION) + " = '13' AND " + q(COL_TOMO) + " IS NOT NULL AND " + q(COL_TOMO) + " != ''")
            online_rm = cursor.fetchone()[0]
        else:
            online_rm = 0
    else:
        total_rm = 0
        online_rm = 0
    conn.close()
    return {"nacional": {"total": total_nacional, "online": online_nacional, "porcentaje": round(online_nacional / total_nacional * 100, 2) if total_nacional > 0 else 0}, "rm": {"total": total_rm, "online": online_rm, "porcentaje": round(online_rm / total_rm * 100, 2) if total_rm > 0 else 0}}

@app.get("/api/ubicacion/{codigo}")
def get_ubicacion(codigo: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ubicaciones WHERE codigo = ?", (codigo,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"error": "Ubicacion no encontrada"}

@app.get("/api/online/{anio}/{rbd}")
def get_online(anio: str, rbd: str):
    conn = get_db()
    cursor = conn.cursor()
    anio_str = str(anio).strip()
    rbd_str = str(rbd).strip()
    cursor.execute("SELECT * FROM online WHERE CAST(anio AS TEXT) = ? AND CAST(rbd AS TEXT) = ? ORDER BY curso, letra", (anio_str, rbd_str))
    rows = cursor.fetchall()
    if len(rows) == 0:
        try:
            anio_num = int(anio_str)
            rbd_num = int(rbd_str)
            cursor.execute("SELECT * FROM online WHERE anio = ? AND rbd = ? ORDER BY curso, letra", (anio_num, rbd_num))
            rows = cursor.fetchall()
        except ValueError:
            pass
    conn.close()

    resultados = []
    for row in rows:
        d = dict(row)
        if COL_OBSERVACIONES_ONLINE and COL_OBSERVACIONES_ONLINE in d:
            d["observaciones"] = d[COL_OBSERVACIONES_ONLINE]
        # NUEVO: Agregar la URL detectada automáticamente
        if COL_URL and COL_URL in d:
            d["url_sharepoint"] = d[COL_URL]
        resultados.append(d)

    return {"resultados": resultados, "total": len(resultados)}

@app.get("/api/establecimiento/{rbd}")
def get_establecimiento(rbd: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico WHERE " + q(COL_RBD) + " = ? ORDER BY " + q(COL_ANIO) + " DESC", (rbd,))
    rows = cursor.fetchall()
    conn.close()
    return {"resultados": [dict(row) for row in rows], "total": len(rows)}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
