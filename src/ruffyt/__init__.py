from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path


def _find_project_root() -> Path:
    """
    Starting from the current working directory, walk upwards until a
    pyproject.toml is found. This makes the script independent of its
    own file location.
    """
    path = Path.cwd().resolve()
    for candidate_dir in (path, *path.parents):
        candidate = candidate_dir / "pyproject.toml"
        if candidate.exists():
            return candidate_dir

    print("No pyproject.toml found upwards from current working directory.")
    raise SystemExit(1)


def _get_direct_dependency_names(pyproject_path: Path) -> set[str]:
    """
    Read [project].dependencies from pyproject.toml and extract only the
    package names (without version / extras).
    """
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    deps = data.get("project", {}).get("dependencies", [])
    names: set[str] = set()

    for dep in deps:
        # Examples:
        #   "fastapi==0.120.2"
        #   "uvicorn[standard]>=0.30"
        token = dep
        # Strip extras: "uvicorn[standard]>=0.30" -> "uvicorn>=0.30"
        if "[" in token:
            token = token.split("[", 1)[0]
        # Cut everything from the first version operator onwards
        for sep in ("<", ">", "=", "!", "~", " "):
            if sep in token:
                token = token.split(sep, 1)[0]
        name = token.strip()
        if name:
            names.add(name)
    return names


def _update_pyproject_dependencies_block(
    pyproject_path: Path, new_versions: dict[str, str]
) -> None:
    """
    Replace the dependencies block in pyproject.toml so that direct dependencies
    are written with the new versions.

    new_versions: mapping { package_name -> version_string (e.g. "0.121.2") }.
    """
    text = pyproject_path.read_text(encoding="utf-8")

    # Find the dependencies block: dependencies = [ ... ]
    pattern = re.compile(r"dependencies\s*=\s*\[(.*?)\]", re.DOTALL)
    match = pattern.search(text)
    if not match:
        print("Kein [project].dependencies Block in pyproject.toml gefunden.")
        raise SystemExit(1)

    # Parse the whole TOML structurally so we can reliably map names.
    data = tomllib.loads(text)
    deps = data.get("project", {}).get("dependencies", [])

    updated_deps: list[str] = []
    for dep in deps:
        token = dep
        base = token
        if "[" in base:
            base = base.split("[", 1)[0]
        for sep in ("<", ">", "=", "!", "~", " "):
            if sep in base:
                base = base.split(sep, 1)[0]
        name = base.strip()

        if name in new_versions:
            # Write conservatively as "name==version"
            new_dep = f"{name}=={new_versions[name]}"
            updated_deps.append(new_dep)
        else:
            # Keep original entry unchanged
            updated_deps.append(dep)

    # Build new dependencies block
    deps_lines = ["dependencies = ["]
    for d in updated_deps:
        deps_lines.append(f'    "{d}",')
    deps_lines.append("]")
    new_block = "\n".join(deps_lines)

    # Replace old block in raw text
    start, end = match.span()
    new_text = text[:start] + new_block + text[end:]
    pyproject_path.write_text(new_text, encoding="utf-8")


def main() -> None:
    project_root = _find_project_root()
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"pyproject.toml nicht gefunden unter {pyproject_path}")
        raise SystemExit(1)

    direct_deps = _get_direct_dependency_names(pyproject_path)
    if not direct_deps:
        print("Keine direkten Dependencies in pyproject.toml gefunden.")
        return

    print(f"Direkte Dependencies: {', '.join(sorted(direct_deps))}")

    # 1. Get outdated packages as JSON (from the current environment)
    result = subprocess.run(
        ["uv", "pip", "list", "--outdated", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    outdated = json.loads(result.stdout)

    # 2. Only update packages that are direct dependencies in pyproject
    to_update = [pkg for pkg in outdated if pkg["name"] in direct_deps]

    if not to_update:
        print("Keine veralteten direkten Dependencies gefunden.")
        return

    new_versions: dict[str, str] = {}
    for pkg in to_update:
        name = pkg["name"]
        current = pkg["version"]
        latest = pkg["latest_version"]
        print(f"{name}: {current} -> {latest}")
        new_versions[name] = latest

    # 3. Patch pyproject.toml
    _update_pyproject_dependencies_block(pyproject_path, new_versions)

    print("pyproject.toml aktualisiert.")
    print("Wenn du das Env anpassen willst, danach z. B.:")
    print("  uv sync")
    print("oder")
    print("  uv lock --upgrade")


if __name__ == "__main__":
    main()
