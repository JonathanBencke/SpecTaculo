"""Configuração do pytest para o projeto SpecTaculo.

Permite que os testes importem os módulos sob `src/` diretamente
(gerador e schema) sem exigir um pacote instalado.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
