from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CREE_ENV_ROOT = ROOT_DIR / "environments" / "cree1865_dictionary_qa"
if str(CREE_ENV_ROOT) not in sys.path:
    sys.path.insert(0, str(CREE_ENV_ROOT))

from cree1865_dictionary_qa.environment import (  # noqa: E402
    DEFAULT_SYSTEM_PROMPT as CREE_DEFAULT_SYSTEM_PROMPT,
    CreeDictionaryRubric,
)


def create_cree_rubric() -> CreeDictionaryRubric:
    return CreeDictionaryRubric()


__all__ = ["CREE_DEFAULT_SYSTEM_PROMPT", "CreeDictionaryRubric", "create_cree_rubric"]
