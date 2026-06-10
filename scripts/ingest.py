from __future__ import annotations

import json

from app.services.ingestion import ingest_pdf


def main() -> None:
    result = ingest_pdf(force_reindex=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

