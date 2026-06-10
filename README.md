# Tenerife RAG App

Aplicación conversacional sobre Tenerife basada en RAG, con:

- **FastAPI** como backend
- **Streamlit** como frontend principal
- **PostgreSQL + pgvector** para persistencia vectorial
- **Prometheus + Grafana** para observabilidad

La base documental inicial es `data\TENERIFE.pdf`.

## Estado actual

El proyecto ya incluye:

- chat conversacional con memoria por sesión
- respuestas documentales con citas
- consulta de clima integrada
- ingesta idempotente del PDF
- entorno de desarrollo ligero
- despliegue con Docker Compose
- métricas Prometheus y dashboard inicial en Grafana
- docstrings en la API principal y soporte para documentación con Sphinx

## Arquitectura

### Backend
- `app\main.py` arranca FastAPI
- `app\services\chat.py` orquesta RAG + clima
- `app\db\*` gestiona PostgreSQL y pgvector
- `app\services\ingestion.py` indexa el PDF

### Frontend
- `streamlit_app.py` es la UI principal
- FastAPI lanza automáticamente Streamlit al arrancar con `uvicorn`
- la raíz `http://localhost:8000` redirige a la UI Streamlit

### Observabilidad
- `/metrics` expone métricas Prometheus
- `prometheus\prometheus.yml` configura scraping
- `grafana\` contiene datasource, provisioning y dashboard

## Configuración

1. Copia `.env.example` a `.env`.
2. Define como mínimo:

```env
GOOGLE_API_KEY=tu_clave
GENERATION_MODEL=gemini-2.5-flash-lite
EMBEDDING_MODEL=models/gemini-embedding-001
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenerife_app
```

> La aplicación prioriza los valores definidos en `.env` sobre variables del shell.

## Instalación local

```powershell
python -m pip install -e .[dev]
```

## Ejecución local

Lanza solo FastAPI; el proceso levantará Streamlit automáticamente:

```powershell
uvicorn app.main:app --reload
```

Accesos:

- UI principal: `http://localhost:8000`
- Streamlit directo: `http://localhost:8501`
- API/health: `http://localhost:8000/health`
- métricas: `http://localhost:8000/metrics`

## Entorno de desarrollo rápido

Si no quieres reconstruir contenedores en cada cambio:

1. Instala dependencias:

```powershell
python -m pip install -e .[dev]
```

2. Levanta solo PostgreSQL + pgvector:

```powershell
docker compose -f docker-compose.dev.yml up -d db
```

O con el helper:

```powershell
.\scripts\dev-up.ps1
```

Si además quieres observabilidad en desarrollo:

```powershell
.\scripts\dev-up.ps1 -WithObservability
```

3. Arranca la aplicación:

```powershell
uvicorn app.main:app --reload
```

4. Cuando termines:

```powershell
.\scripts\dev-down.ps1
```

Si has levantado observabilidad en desarrollo:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- credenciales: `admin` / `admin`

## Docker Compose

Levanta toda la solución:

```powershell
docker compose up --build
```

Servicios disponibles:

| Servicio | URL | Notas |
| --- | --- | --- |
| UI principal | `http://localhost:8000` | Redirige a Streamlit |
| Streamlit | `http://localhost:8501` | UI servida por el proceso lanzado desde FastAPI |
| API FastAPI | `http://localhost:8000` | Backend |
| Prometheus | `http://localhost:9090` | Scraping de `/metrics` |
| Grafana | `http://localhost:3000` | Usuario `admin`, contraseña `admin` |

## Observabilidad

Grafana queda provisionado automáticamente con:

- datasource Prometheus
- carpeta de dashboards
- dashboard inicial `Tenerife RAG Observability`

Métricas expuestas actualmente:

- `http_requests_total`
- `http_request_duration_seconds`
- `chat_turns_total`
- `llm_requests_total`
- `llm_input_tokens_total`
- `llm_output_tokens_total`
- `llm_total_tokens_total`
- `llm_request_duration_seconds`
- `chat_source_count`
- `weather_tool_calls_total`

## Documentación técnica

Instala dependencias de desarrollo y genera la documentación HTML con Sphinx:

```powershell
python -m pip install -e .[dev]
python -m sphinx -b html docs docs\_build\html
```

El resultado queda en `docs\_build\html\index.html`.

## Guía rápida para cargar más de un PDF en pgvector

### Qué módulo hace la ingesta

El módulo principal es **`app\services\ingestion.py`**.

Su flujo actual es:

1. lee la ruta configurada en `Settings.data_pdf_path`
2. calcula checksum del PDF
3. carga páginas con `app\services\documents.py`
4. divide el contenido en chunks
5. genera embeddings
6. guarda documento y chunks con `app\db\repositories.py`

Puntos clave:

- `app\services\documents.py` carga y trocea PDFs
- `app\services\ingestion.py` orquesta la indexación
- `app\db\repositories.py` persiste `documents` y `chunks`
- `scripts\ingest.py` es la entrada manual para lanzar la ingesta

### Limitación actual

Ahora mismo el proyecto está preparado para **un único PDF principal** porque `ingest_pdf()` trabaja con `settings.data_pdf_path`.

### Qué habría que cambiar para soportar varios PDFs

La forma más simple es convertir la ingesta en un flujo por documento.

#### 1. Permitir varias rutas o un directorio

En `app\core\config.py`, cambiar la configuración para usar por ejemplo:

- `data_dir: Path = PROJECT_ROOT / "data"`

o una lista explícita:

- `data_pdf_paths: list[Path]`

#### 2. Generalizar la función de ingesta

En `app\services\ingestion.py`, separar la lógica actual en dos funciones:

- `ingest_document(pdf_path: Path, force_reindex: bool = True) -> dict`
- `ingest_all_pdfs(force_reindex: bool = True) -> list[dict]`

`ingest_document()` reutilizaría casi todo el código actual, pero usando el `pdf_path` recibido en lugar de `settings.data_pdf_path`.

`ingest_all_pdfs()` solo tendría que recorrer `data_dir.glob("*.pdf")` e invocar `ingest_document()` para cada fichero.

#### 3. Mantener el control por documento en base de datos

La base ya está casi lista para varios PDFs porque:

- `documents.source_name` identifica cada documento
- `chunks.source_name` relaciona cada chunk con su PDF
- `chunk_key` ya se construye como `source_name:chunk_id`

Eso significa que no hace falta rediseñar el esquema para empezar a trabajar con múltiples documentos.

#### 4. Adaptar el script manual

En `scripts\ingest.py`, lo más útil sería permitir dos modos:

- indexar un único fichero
- indexar todos los PDFs de `data\`

Una versión mínima sería:

```python
from app.services.ingestion import ingest_all_pdfs


def main() -> None:
    results = ingest_all_pdfs(force_reindex=True)
    ...
```

### Qué módulos tocaría un desarrollador nuevo

| Archivo | Cambio |
| --- | --- |
| `app\core\config.py` | añadir `data_dir` o lista de PDFs |
| `app\services\ingestion.py` | extraer ingesta por fichero y bucle por carpeta |
| `scripts\ingest.py` | permitir ingesta múltiple |
| `app\services\chat.py` | sin cambios grandes; ya consulta todos los chunks almacenados |
| `app\db\repositories.py` | probablemente sin cambios para un primer soporte multi-PDF |

### Forma más ágil de añadir información a la base vectorial

Sí: la vía más ágil es **usar una carpeta `data\` como entrada** y ejecutar una ingesta por lote.

Flujo recomendado:

1. copiar nuevos PDFs a `data\`
2. lanzar `python scripts\ingest.py`
3. dejar que la lógica idempotente reindexe solo los documentos que cambien

Para hacerlo todavía más cómodo, se puede añadir después:

- un endpoint `POST /api/v1/ingest?all=true`
- soporte para subir PDFs desde la UI o desde un endpoint admin
- un watcher local que reindexe automáticamente cuando aparezcan nuevos ficheros

### Recomendación práctica

Si alguien entra nuevo al proyecto, el cambio más rentable es este:

1. convertir `ingest_pdf()` en `ingest_document(pdf_path, ...)`
2. añadir `ingest_all_pdfs()`
3. usar `data\*.pdf` como convención

Con eso el proyecto pasa de un corpus único a un corpus multi-documento sin tocar la búsqueda vectorial ni el esquema principal.

## Comandos útiles

```powershell
ruff check .
pytest
docker compose config
python -m pip install -e .[dev]
python -m sphinx -b html docs docs\_build\html
```

## Estructura principal

```text
app/
  api/
  core/
  db/
  services/
  ui/
grafana/
prometheus/
scripts/
streamlit_app.py
docker-compose.yml
docker-compose.dev.yml
```

## Notas

- Si la base vectorial está vacía, el backend intentará indexar `data\TENERIFE.pdf` automáticamente.
- La UI estática anterior ya no forma parte del proyecto.
