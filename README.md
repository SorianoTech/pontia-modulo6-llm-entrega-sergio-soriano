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

## Tests

```powershell
pytest
```

