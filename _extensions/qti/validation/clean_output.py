"""Pre-render hook: empty the configured Quarto project output directory."""

import os
import pathlib
import shutil
import sys


def clean_output_dir():
    configured = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    if not configured:
        return

    project_dir = pathlib.Path.cwd().resolve()
    output_dir = pathlib.Path(configured).resolve()
    if output_dir == output_dir.parent or output_dir == project_dir or output_dir in project_dir.parents:
        raise ValueError(f"refusing to clean an unsafe output directory: {output_dir}")
    if not output_dir.exists():
        return

    for entry in output_dir.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def main():
    try:
        clean_output_dir()
    except (OSError, ValueError) as error:
        print(f"Cannot clean Quarto output directory: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())