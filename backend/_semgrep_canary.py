"""TEMPORARY -- DELETE THIS FILE.

Deliberately insecure code, added only to prove that the Semgrep job in
.github/workflows/ci.yml really does report findings and fail the build on
high-severity ones. It is expected to turn CI red.

Nothing imports this module, so none of it ever runs.

To remove it, see "Removing the Semgrep canary" in the commit that added it:

    git revert <that commit>

or delete the two canary files by hand:

    rm backend/_semgrep_canary.py frontend/src/_semgrep_canary.js
"""

import hashlib
import subprocess


def hash_password(password: str) -> str:
    """MD5 is not a password hash -- weak cryptographic algorithm."""
    return hashlib.md5(password.encode()).hexdigest()


def run_calculation(expression: str):
    """eval on caller-supplied input -- arbitrary code execution."""
    return eval(expression)


def list_directory(path: str) -> int:
    """String-built shell command -- command injection."""
    return subprocess.call("ls -la " + path, shell=True)
