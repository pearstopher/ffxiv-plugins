"""Load config.json, which controls which repos are combined."""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path("config.json")


@dataclass(frozen=True)
class Config:
    owner: str
    topic: str = "dalamud-plugin"
    include: tuple[str, ...] = ()  # repo names added even without the topic
    exclude: tuple[str, ...] = ()  # repo names always skipped
    filenames: tuple[str, ...] = ("repo.json",)  # plugin JSON files to try, in order


def load_config(path: Path = CONFIG_PATH) -> Config:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Config(**{key: tuple(v) if isinstance(v, list) else v for key, v in data.items()})
