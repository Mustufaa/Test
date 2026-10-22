"""Intentionally vulnerable toy code for security testing only.

Do not use this pattern in production.
"""


def find_user(connection, username):
	"""Vulnerability: SQL injection through string interpolation."""
	query = f"SELECT id, name FROM users WHERE name = '{username}'"
	return connection.execute(query).fetchall()


if __name__ == "__main__":
	print("Intentionally vulnerable test fixture; use only in an isolated environment.")
