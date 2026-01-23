import os import typer from pathlib 
import Path from forgeops.core.file_utils 
import write_file from forgeops.templates.dockerfile_template 
import get_template as get_dockerfile from forgeops.templates.gitignore_template 
import get_template as get_gitignore

def init_project(project_name: str): 
  """Initialize a new project with basic files."""
  project_path = Path(project_name) 
  if project_path.exists(): 
    typer.echo(f"Project '{project_name}' already exists.") 
    return
