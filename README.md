# 🏫 Sistema de Búsqueda de Establecimientos

Aplicación web que reemplaza las macros perdidas de tu Excel `Directorio_Historico_Buscador.xlsx`.

## 📦 Contenido

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Servidor backend (FastAPI) |
| `directorio.db` | Base de datos SQLite con todos los datos |
| `static/index.html` | Frontend web (interfaz de usuario) |
| `requirements.txt` | Dependencias Python |

## 🚀 Instalación y ejecución

### 1. Requisitos
- Python 3.8 o superior
- pip

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python app.py
```

### 4. Abrir en navegador
```
http://localhost:8000
```

## ✨ Funcionalidades

| Función | Descripción |
|---------|-------------|
| 🔍 Buscador Específico | Busca por **Año + RBD** (exacto) |
| 🔎 Buscador por Nombre | Búsqueda parcial con límite de 1,000 resultados |
| 📊 Progreso Nacional | Barra con % de establecimientos digitalizados (ONLINE) |
| 🏙️ Progreso RM | Barra con % de la Región Metropolitana |
| 💻 Ver ONLINE | Muestra actas digitalizadas con enlaces directos |
| 📍 Ver Ubicación | Muestra piso, sala, sector y mapa visual de ubicación |

## 📁 Datos incluidos

- **HISTÓRICO**: 30,676 registros de establecimientos
- **ONLINE**: 2,886 actas digitalizadas con enlaces
- **UBICACIONES**: 149 códigos de ubicación física

## 🔧 Solución de problemas

**Puerto ocupado**: Si el puerto 8000 está en uso, edita `app.py` y cambia:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Cambia 8000 por otro puerto
```

**No se ven los datos**: Verifica que `directorio.db` esté en la misma carpeta que `app.py`.

## 📝 Notas

- La base de datos SQLite pesa muy poco y no requiere servidor de base de datos.
- Las búsquedas son instantáneas gracias a los índices creados.
- El frontend es 100% responsive y funciona en celulares.
