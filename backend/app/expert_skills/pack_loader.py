from functools import lru_cache
from pathlib import Path

PACKS_ROOT = Path(__file__).resolve().parent / "packs"


@lru_cache
def load_skill_pack(slug: str) -> dict:
    pack_dir = PACKS_ROOT / slug
    if not pack_dir.is_dir():
        raise FileNotFoundError(f"Expert skill pack '{slug}' not found at {pack_dir}")

    skill_md = (pack_dir / "SKILL.md").read_text(encoding="utf-8")
    references: dict[str, str] = {}
    refs_dir = pack_dir / "references"
    if refs_dir.is_dir():
        for path in sorted(refs_dir.glob("*.md")):
            references[path.name] = path.read_text(encoding="utf-8")

    return {"skill_md": skill_md, "references": references}


def reference_summary(slug: str, *, max_chars: int = 12000) -> str:
    pack = load_skill_pack(slug)
    parts = [pack["skill_md"]]
    for name, content in pack["references"].items():
        parts.append(f"\n\n## Reference: {name}\n{content}")
    combined = "".join(parts)
    if len(combined) <= max_chars:
        return combined
    return combined[: max_chars - 3] + "..."