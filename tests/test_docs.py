import re
from pathlib import Path

import pytest

DOCS = [Path("README.md"), *Path("docs").glob("*.md")]
LINK = re.compile(r"\]\(([^)\s]+)\)")


def local_links(doc: Path) -> list[str]:
    """Relative link targets in a Markdown file, without #anchors."""
    targets = (match.split("#")[0] for match in LINK.findall(doc.read_text(encoding="utf-8")))
    return [t for t in targets if t and not t.startswith(("http://", "https://", "mailto:"))]


@pytest.mark.parametrize("doc", DOCS, ids=str)
def test_relative_links_point_to_existing_files(doc):
    missing = [t for t in local_links(doc) if not (doc.parent / t).exists()]
    assert not missing, f"{doc} links to missing files: {missing}"


def test_maintaining_links_to_plugin_setup():
    assert "plugin-setup.md" in local_links(Path("docs/maintaining.md"))
