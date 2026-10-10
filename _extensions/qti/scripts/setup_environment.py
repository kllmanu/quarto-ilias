"""Pre-render hook: prepare the extension's private Python environment."""

import subprocess
import sys
import venv

from environment import REQUIREMENTS, environment_path, environment_python, environment_ready


def main():
    environment = environment_path()
    if environment_ready(environment):
        return 0
    print("Setting up QTI Python dependencies (first use or updated requirements)...", file=sys.stderr)
    try:
        venv.EnvBuilder(with_pip=True).create(environment)
        subprocess.run([str(environment_python(environment)), "-m", "pip", "install",
                        "-r", str(REQUIREMENTS)], check=True)
        (environment / ".ready").touch()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"QTI environment setup failed: {error}. "
              "Python must support venv and pip; initial setup requires access to the package index.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())