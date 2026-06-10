# Tenerife RAG App

Aplicacion web conversacional sobre Tenerife basada en el notebook `notebook\rag-tenerife.ipynb`.

## Objetivos

- Mantener el conocimiento turístico del PDF `data\TENERIFE.pdf`.
- Ofrecer chat conversacional con memoria.
- Responder con citas documentales.
- Mantener la consulta de clima `get_weather`.
- Preparar una arquitectura portable con FastAPI, PostgreSQL y pgvector.

## Estado

La base Python del proyecto ya esta modularizada. Las siguientes fases incorporaran:

- persistencia en pgvector,
- API FastAPI,
- frontend web,
- observabilidad,
- Docker y CI.

## Configuracion

1. Crea un fichero `.env` en la raiz del proyecto.
2. Define al menos:

```env
GOOGLE_API_KEY=tu_clave
GENERATION_MODEL=gemini-2.5-flash-lite
EMBEDDING_MODEL=models/gemini-embedding-001
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenerife_app
```

> La aplicacion prioriza los valores definidos en `.env` sobre variables de entorno del shell.

## Instalacion local

```powershell
python -m pip install -e .[dev]
```

## Ejecucion local

Arranca `uvicorn` y el backend lanzará automáticamente Streamlit:

```powershell
uvicorn app.main:app --reload
```

Abre `http://localhost:8000` y serás redirigido a la UI Streamlit.

## Entorno de desarrollo rapido

Si no quieres reconstruir la imagen Docker en cada cambio, usa la base de datos en contenedor y ejecuta solo `uvicorn` en local. El frontend Streamlit se lanzará automáticamente.

1. Copia `.env.example` a `.env`.
2. Instala dependencias:

```powershell
python -m pip install -e .[dev]
```

3. Levanta solo PostgreSQL + pgvector:

```powershell
docker compose -f docker-compose.dev.yml up -d db
```

O con el helper:

```powershell
.\scripts\dev-up.ps1
```

4. Arranca la aplicación:

```powershell
uvicorn app.main:app --reload
```

5. Cuando termines:

```powershell
.\scripts\dev-down.ps1
```

En este modo solo reinicias `uvicorn` y mantienes la base de datos viva en Docker.

## Docker Compose

1. Copia `.env.example` a `.env` y completa `GOOGLE_API_KEY`.
2. Levanta la aplicacion:

```powershell
docker compose up --build
```

3. Abre `http://localhost:8000`; FastAPI arrancará Streamlit y redirigirá la raíz a la UI.
4. Observabilidad:
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000`
   - credenciales por defecto: `admin` / `admin`

La aplicacion arrancara PostgreSQL con pgvector y FastAPI como backend. Al iniciarse `uvicorn`, se levantara automaticamente la UI Streamlit en el mismo contenedor. Además, `docker compose` levanta Prometheus y Grafana ya provisionados para visualizar las métricas del endpoint `/metrics`. Si la base vectorial esta vacia, el backend intentara indexar `data\TENERIFE.pdf` automaticamente.

## Tests

```powershell
pytest
```
