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
- logging estructurado JSON en fichero y Loki
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
GENERATION_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GOOGLE_API_KEY=tu_clave
GENERATION_MODEL=gemini-2.5-flash-lite
EMBEDDING_MODEL=models/gemini-embedding-001
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenerife_app
```

O para usar Ollama:

```env
GENERATION_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
GENERATION_MODEL=tenerife-gemma-4-12b-it
EMBEDDING_MODEL=nomic-embed-text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenerife_app
```

> La aplicación prioriza los valores definidos en `.env` sobre variables del shell.

### Variables de configuración disponibles

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `APP_NAME` | Nombre visible de la aplicación FastAPI/Streamlit. | `Tenerife RAG App` |
| `APP_ENV` | Entorno lógico de ejecución. | `development` |
| `APP_HOST` | Host donde arranca FastAPI. | `0.0.0.0` |
| `APP_PORT` | Puerto del backend FastAPI. | `8000` |
| `STREAMLIT_API_URL` | URL base que usa Streamlit para llamar a la API. | `http://127.0.0.1:8000` |
| `STREAMLIT_SERVER_PORT` | Puerto en el que se expone Streamlit. | `8501` |
| `GENERATION_PROVIDER` | Proveedor del modelo generativo (`gemini` u `ollama`). | `gemini` |
| `EMBEDDING_PROVIDER` | Proveedor de embeddings (`gemini` u `ollama`). | `gemini` |
| `GOOGLE_API_KEY` | Clave de API para Gemini cuando usas ese proveedor. | vacío |
| `GENERATION_MODEL` | Modelo usado por el proveedor generativo activo. | `gemini-2.5-flash-lite` |
| `EMBEDDING_MODEL` | Modelo usado por el proveedor de embeddings activo. | `models/gemini-embedding-001` |
| `OLLAMA_BASE_URL` | URL base del servidor Ollama. | `http://127.0.0.1:11434` |
| `GENERATION_TEMPERATURE` | Temperatura del modelo generativo. | `0.2` |
| `GENERATION_MAX_TOKENS` | Máximo de tokens de salida del LLM. | `1024` |
| `RAG_TOP_K` | Número de chunks recuperados en retrieval. | `4` |
| `CHUNK_SIZE` | Tamaño de chunk en la ingesta documental. | `500` |
| `CHUNK_OVERLAP` | Solape entre chunks consecutivos. | `50` |
| `EMBEDDING_DIMENSIONS` | Dimensión esperada del vector embedding en pgvector. | `3072` |
| `REQUEST_TIMEOUT_SECONDS` | Timeout de llamadas HTTP externas. | `15` |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL. | `postgresql://postgres:postgres@localhost:5432/tenerife_app` |
| `DATA_PDF_PATH` | Ruta del PDF principal a indexar. | `data\\TENERIFE.pdf` |
| `AUDIT_LOG_PATH` | Ruta del fichero JSON de auditoría. | `logs\\app.jsonl` |
| `AUTO_INGEST_ON_STARTUP` | Si la app intenta indexar automáticamente al arrancar. | `true` |
| `WEATHER_LOCATION` | Ubicación base usada para Open-Meteo. | `Tenerife` |
| `OPEN_METEO_GEOCODING_URL` | Endpoint de geocodificación de Open-Meteo. | `https://geocoding-api.open-meteo.com/v1/search` |
| `OPEN_METEO_FORECAST_URL` | Endpoint de predicción meteorológica de Open-Meteo. | `https://api.open-meteo.com/v1/forecast` |

Las variables más habituales ya aparecen en `.env.example`, pero la tabla anterior refleja toda la superficie configurable definida en `app\core\config.py`.

### Variables extra para `docker-compose.ollama.yml`

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `OLLAMA_CHAT_MODEL` | Nombre local con el que Ollama registra el modelo GGUF importado. | `tenerife-gemma-4-12b-it` |
| `OLLAMA_MODEL_SOURCE_URL` | URL del GGUF que se descarga al inicializar Ollama. | `https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/main/MTP/gemma-4-12b-it-Q8_0-MTP.gguf?download=true` |
| `OLLAMA_MODEL_FILENAME` | Nombre del fichero GGUF guardado en el volumen compartido. | `gemma-4-12b-it-Q8_0-MTP.gguf` |
| `OLLAMA_EMBEDDING_MODEL` | Modelo de embeddings que se hace `pull` en Ollama. | `nomic-embed-text` |
| `HF_TOKEN` | Token opcional de Hugging Face si necesitas autenticación para descargar el GGUF. | vacío |

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
- Loki: `http://localhost:3100`
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
| Loki | `http://localhost:3100` | Agregación de logs |

### Docker Compose con Ollama

Si quieres levantar también **Ollama** y que la aplicación use modelos locales, arranca la pila combinando ambos ficheros:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build
```

Este overlay:

- añade el servicio `ollama`
- descarga por defecto el GGUF de **Unsloth Gemma 4 12B IT**
- crea el modelo local `tenerife-gemma-4-12b-it`
- hace `pull` del modelo de embeddings `nomic-embed-text`
- reconfigura el backend para usar `GENERATION_PROVIDER=ollama` y `EMBEDDING_PROVIDER=ollama`

La primera puesta en marcha puede tardar bastante porque descarga e importa el modelo GGUF.

## Observabilidad

Grafana queda provisionado automáticamente con:

- datasource Prometheus
- datasource Loki
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

Logs de auditoría:

- fichero JSON local: `logs\app.jsonl`
- visibles en Grafana mediante el panel **Audit Logs**
- consultables también en **Explore** usando la datasource **Loki**
- incluyen mensaje del usuario, prompt enviado al LLM, respuesta final y contenido de los chunks recuperados

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
