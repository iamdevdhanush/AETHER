import typer 
import re from pathlib 
import Path

def lint_dockerfile():
  """Lint the Dockerfile for common issues."""
  dockerfile_path = Path("Dockerfile") 
  if not dockerfile_path.exists(): 
    typer.echo("No Dockerfile found in the current directory.") 
    return
    
content = dockerfile_path.read_text()
warnings = []

# Check for 'latest' tag usage
if re.search(r'FROM\s+.*:latest', content, re.IGNORECASE):
    warnings.append("Warning: Using 'latest' tag in FROM instruction. Consider pinning to a specific version.")

if warnings:
    for warning in warnings:
        typer.echo(warning)
else:
    typer.echo("Dockerfile looks good!")
