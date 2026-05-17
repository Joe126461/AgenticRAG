from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def resolve_workspace_path(*parts: str) -> Path:
    return WORKSPACE_ROOT.joinpath(*parts)
