Uso de la documentacion
=======================

La documentacion se genera con Sphinx a partir de docstrings del codigo Python y de estas paginas reStructuredText.

Generar HTML
------------

.. code-block:: powershell

   python -m sphinx -b html docs docs\_build\html

La salida queda en ``docs\_build\html\index.html``.
