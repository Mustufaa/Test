"""Intentionally vulnerable toy code for security testing only.

Do not use this pattern in production.
"""

import subprocess


def run_local_command(user_input):
	"""Vulnerability: command injection via shell=True."""
	return subprocess.run(f"echo {user_input}", shell=True, capture_output=True, text=True)


if __name__ == "__main__":
	print("Intentionally vulnerable test fixture; use only in an isolated environment.")
