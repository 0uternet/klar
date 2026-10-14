"""Print the dependency requirements declared in pyproject.toml, one per line.

Used by the Dockerfile to install third-party dependencies in their own (cached)
layer before the klar source is copied, and by CI to install dev dependencies.
Standard library only (tomllib, Python >= 3.11).

usage: python3 pyproject_deps.py runtime|dev [path/to/pyproject.toml]

  runtime  [project].dependencies
  dev      [project.optional-dependencies] dev / test / tests
           + [dependency-groups] dev / test / tests (PEP 735)
"""

from __future__ import annotations

import re
import sys
import tomllib

GROUPS = ("dev", "test", "tests")


def _name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return re.sub(r"[-_.]+", "-", match.group(1)).lower() if match else ""


def _group(groups: dict, name: str, seen: set[str]) -> list[str]:
    """Resolve a PEP 735 dependency group, following {include-group = ...} entries."""
    if name in seen:
        return []
    seen.add(name)
    out: list[str] = []
    for item in groups.get(name, []):
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and "include-group" in item:
            out.extend(_group(groups, item["include-group"], seen))
    return out


def main() -> int:
    kind = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    path = sys.argv[2] if len(sys.argv) > 2 else "pyproject.toml"
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    project = data.get("project", {})

    if kind == "runtime":
        reqs = list(project.get("dependencies", []))
    elif kind == "dev":
        optional = project.get("optional-dependencies", {})
        groups = data.get("dependency-groups", {})
        reqs = []
        for group in GROUPS:
            reqs += optional.get(group, [])
            reqs += _group(groups, group, set())
    else:
        print(__doc__, file=sys.stderr)
        return 2

    own = _name(project.get("name", ""))
    printed: set[str] = set()
    for req in reqs:
        req = req.strip()
        # Skip self references such as "klar[test]": the package itself is installed separately.
        if not req or (own and _name(req) == own) or req in printed:
            continue
        printed.add(req)
        print(req)
    return 0


if __name__ == "__main__":
    sys.exit(main())
