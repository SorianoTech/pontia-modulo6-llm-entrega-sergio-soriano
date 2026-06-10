"""Sphinx configuration for the Tenerife RAG application."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

project = "Tenerife RAG App"
author = "sorianoacens"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_typehints = "description"
autodoc_member_order = "bysource"
html_theme = "alabaster"
