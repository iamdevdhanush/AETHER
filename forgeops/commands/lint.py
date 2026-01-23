import typer 
import re from pathlib 
import Path

def lint_dockerfile():
  """Lint the Dockerfile for common issues."""
  dockerfile_path = Path("Dockerfile") 
  if not dockerfile_path.exists(): 
    typer.echo("No Dockerfile found in the current directory.") 
    return
