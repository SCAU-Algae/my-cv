#!/usr/bin/env python3
"""Build local HTML assets and, when possible, a PDF CV."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent
BUILD_HTML = ROOT / "_build" / "html"
FONTS_DIR = ROOT / "fonts"
PYTHON_EXE = Path(sys.executable) if sys.executable else None


def run(command: list[str], *, check: bool = True) -> int:
    """Run a subprocess and stream output."""
    print(f"\n>>> {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def command_exists(name: str) -> bool:
    """Check if a command exists on PATH."""
    return shutil.which(name) is not None


def python_command() -> list[str] | None:
    """Return the current Python executable when available."""
    if PYTHON_EXE and PYTHON_EXE.exists():
        return [str(PYTHON_EXE)]
    if command_exists("python"):
        return ["python"]
    return None


def try_build_pdf() -> bool:
    """Build cv.typ and cv.pdf when local dependencies are available."""
    python_cmd = python_command()
    if not python_cmd:
        print("! Skipping PDF generation: python not found on PATH.")
        return False

    run([*python_cmd, "generate_cv.py"])

    if not command_exists("typst"):
        print("! Generated cv.typ, but skipped cv.pdf: typst not found on PATH.")
        return False

    if not FONTS_DIR.exists():
        print("! Generated cv.typ, but skipped cv.pdf: ./fonts directory not found.")
        return False

    run(
        [
            "typst",
            "compile",
            "cv.typ",
            "cv.pdf",
            "--font-path",
            str(FONTS_DIR),
            "--ignore-system-fonts",
        ]
    )
    return True


def main() -> None:
    """Build local artifacts."""
    if not command_exists("myst"):
        print("! myst command not found on PATH.")
        print("  Install with: npm install -g mystmd")
        raise SystemExit(1)

    pdf_built = try_build_pdf()

    run(["myst", "build", "--html"])

    if pdf_built and BUILD_HTML.exists():
        shutil.copy2(ROOT / "cv.pdf", BUILD_HTML / "cv.pdf")
        print(f"Copied cv.pdf to {BUILD_HTML / 'cv.pdf'}")
    else:
        print("! HTML built, but cv.pdf was not copied because no PDF was generated.")

    print("\nBuild finished.")
    print(f"- HTML: {BUILD_HTML}")
    if (ROOT / "cv.typ").exists():
        print(f"- Typst source: {ROOT / 'cv.typ'}")
    if (ROOT / "cv.pdf").exists():
        print(f"- PDF: {ROOT / 'cv.pdf'}")


if __name__ == "__main__":
    main()
