import subprocess

tracked = subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", "HEAD"],
    text=True,
).splitlines()

bad = [
    path for path in tracked
    if "/__pycache__/" in f"/{path}"
    or path.endswith((".pyc", ".pyo"))
    or ".egg-info/" in path
]

assert ".gitignore" in tracked, ".gitignore is not committed"
assert not bad, "Generated files remain tracked:\n" + "\n".join(bad)

print("Committed Git tree is clean.")
