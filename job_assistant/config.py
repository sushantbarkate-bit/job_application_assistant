from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

# Config keys that hold file or folder paths, relative to the project root.
PATH_KEYS = [
    ("profile", "resume_path"),
    ("workflow", "database_path"),
    ("workflow", "report_dir"),
    ("workflow", "output_dir"),
]


def _resolve(value: str) -> str:
    path = Path(value)
    return str(path if path.is_absolute() else ROOT / path)


def load_config(path: str | Path = ROOT / "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Resolve paths against the project root so commands work from any folder.
    for section, key in PATH_KEYS:
        value = (cfg.get(section) or {}).get(key)
        if value:
            cfg[section][key] = _resolve(value)

    return cfg
