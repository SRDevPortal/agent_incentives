import ast
import json
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in root.rglob("*.py"):
    if "__pycache__" not in str(p):ast.parse(p.read_text(),filename=str(p))
for p in (root/"agent_incentives").rglob("*.json"):json.loads(p.read_text())
for p in (root/"agent_incentives").rglob("*.js"):
    subprocess.run(["node","--check",str(p)],check=True)
print("Python, JSON and JavaScript checks passed")
