"""
Utility functions for normalizing parameter aliases across tools.

Provide simple, well-tested helpers that map common alias names (e.g. 'path',
'file_path', 'directory', 'dir') to canonical argument names expected by tool
implementations. This centralizes the logic and keeps tools simple.
"""
from typing import Dict, Iterable, Any


def normalize_params(params: Dict[str, Any], mappings: Dict[str, Iterable[str]]) -> Dict[str, Any]:
    """
    Normalize parameter dictionary in-place (returns a new dict) according
    to provided mappings.

    - params: the incoming kwargs dict from caller/planner
    - mappings: a dict where keys are canonical names and values are comma-separated
      alias names (or a list/tuple). Example:
        {"file_path": ["path", "file_path"], "content": ["content"]}

    The function will prefer an existing canonical key if present. Otherwise it
    will search aliases in order and set the canonical key to the first found.
    """
    normalized = dict(params) if params is not None else {}

    for canonical, aliases in mappings.items():
        # normalize aliases to a list
        if isinstance(aliases, str):
            alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
        else:
            alias_list = list(aliases)

        # if canonical already present, skip
        if canonical in normalized:
            continue

        # find first alias present
        for alias in alias_list:
            if alias in normalized:
                normalized[canonical] = normalized.pop(alias)
                break

    return normalized
