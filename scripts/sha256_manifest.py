from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MANIFEST_SHA256.txt"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


files = [p for p in ROOT.rglob("*") if p.is_file() and p != OUT and ".git" not in p.parts]
with OUT.open("w", encoding="utf-8", newline="\n") as handle:
    for path in sorted(files):
        handle.write(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n")
print(f"Wrote {len(files)} entries to {OUT}")
