# Guía simple de endpoints

Este documento resume qué hace cada endpoint expuesto actualmente por la aplicación.

## `GET /`

Redirige al frontend de **Streamlit**.

- no devuelve contenido propio de la API
- responde con una redirección `307`
- su objetivo es llevar al usuario a la interfaz web

## `GET /health`

Devuelve un estado simple para comprobar que el backend está vivo.

Respuesta típica:

```json
{
  "status": "ok"
}
```

Uso habitual:

- healthchecks de Docker
- comprobaciones rápidas desde navegador, `curl` o monitorización

## `GET /metrics`

Expone las métricas de **Prometheus** del backend.

Qué hace al llamarlo:

- genera el payload de métricas actual
- devuelve contadores e histogramas del servicio
- sirve como punto de scraping para Prometheus

Ejemplos de datos expuestos:

- requests HTTP
- latencias
- turnos de chat
- uso del LLM
- tokens
- uso de la tool de clima

## `GET /api/v1/info`

Devuelve las tarjetas informativas que se muestran en la portada de la aplicación.

Qué hace al llamarlo:

- carga el contenido estático definido en `app\services\content.py`
- devuelve una lista de tarjetas con `title` y `description`

Uso habitual:

- poblar la home de Streamlit
- mostrar contenido fijo sobre Tenerife

## `POST /api/v1/chat`

Es el endpoint principal del asistente conversacional.

Qué hace al llamarlo:

1. valida el cuerpo de la petición
2. asegura que exista una sesión de conversación
3. recupera historial reciente
4. decide si debe usar:
   - RAG
   - tool de clima
   - o ambos
5. si aplica, recupera chunks desde pgvector
6. si aplica, consulta Open-Meteo
7. construye el prompt
8. llama al modelo LLM configurado
9. guarda mensajes y metadatos en base de datos
10. devuelve respuesta, fuentes y datos de clima si existen

Cuerpo esperado:

```json
{
  "message": "¿Qué puedo ver en La Laguna?",
  "session_id": "opcional"
}
```

Respuesta típica:

```json
{
  "session_id": "uuid",
  "answer": "respuesta generada",
  "sources": [
    {
      "source": "TENERIFE.pdf",
      "page": 9,
      "chunk_id": 13
    }
  ],
  "weather": null,
  "rag_used": true,
  "created_at": "2026-06-11T20:00:00Z",
  "metadata": {}
}
```

Devuelve `503` si falta configuración crítica del proveedor LLM o embeddings.

## `POST /api/v1/ingest`

Lanza manualmente la ingesta del PDF documental.

Qué hace al llamarlo:

1. valida que la configuración del proveedor de embeddings sea usable
2. inicializa la base si hace falta
3. calcula checksum del documento
4. carga el PDF
5. trocea el contenido en chunks
6. genera embeddings
7. guarda documento y chunks en PostgreSQL + pgvector
8. reutiliza el índice existente si el checksum no ha cambiado

Uso habitual:

- forzar una reindexación
- reconstruir la base vectorial
- cargar el corpus antes de usar el chat

Devuelve `503` si falta configuración del proveedor de embeddings.

## Resumen rápido

| Endpoint | Método | Función principal |
| --- | --- | --- |
| `/` | `GET` | Redirigir a Streamlit |
| `/health` | `GET` | Comprobar que el backend está vivo |
| `/metrics` | `GET` | Exponer métricas Prometheus |
| `/api/v1/info` | `GET` | Devolver contenido informativo de la portada |
| `/api/v1/chat` | `POST` | Procesar una consulta conversacional |
| `/api/v1/ingest` | `POST` | Reindexar el corpus documental |
