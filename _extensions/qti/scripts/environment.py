"""Locate the Python environment managed by the extension's setup hook."""

import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"


def environment_path():
    if sys.platform == "win32":
        cache = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        cache = pathlib.Path.home() / "Library" / "Caches"
    else:
        cache = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache"))
    base_python = os.path.realpath(getattr(sys, "_base_executable", sys.executable))
    fingerprint = REQUIREMENTS.read_bytes() + sys.version.encode() + base_python.encode()
    key = hashlib.sha256(fingerprint).hexdigest()[:16]
    return cache / "quarto-qti" / key


def environment_python(environment):
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def environment_ready(environment):
    return environment_python(environment).is_file() and (environment / ".ready").is_file()


def run_in_environment():
    environment = environment_path()
    if pathlib.Path(sys.prefix).resolve() == environment.resolve():
        return
    if not environment_ready(environment):
        print(f"QTI Python environment is not ready. Run {ROOT / 'scripts' / 'setup_environment.py'} "
              "or configure it as the first pre-render hook.", file=sys.stderr)
        sys.exit(1)
    sys.exit(subprocess.call([str(environment_python(environment)), *sys.argv]))