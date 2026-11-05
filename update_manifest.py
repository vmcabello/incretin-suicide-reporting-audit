"""Regenerate the local file inventory; does not commit, tag, or publish anything."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.root.resolve()
    metadata = json.loads((root / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in {".git", "__pycache__", ".venv", "replay"} for part in relative.parts):
            continue
        if relative.as_posix() == "MANIFEST.json" or path.name == ".DS_Store" or path.suffix in {".pyc", ".pyo"}:
            continue
        content = path.read_bytes()
        files.append({"path": relative.as_posix(), "bytes": len(content), "sha256": sha256(content).hexdigest()})
    output = {"version": metadata["version"], "files": files}
    (root / "MANIFEST.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"version": metadata["version"], "manifest_files": len(files), "published": False}))


if __name__ == "__main__":
    main()
