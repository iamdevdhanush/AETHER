import typer from forgeops.commands import init, lint, scan, generate_ci

app = typer.Typer()

app.command()(init.init_project) app.command()(lint.lint_dockerfile) app.command()(scan.scan_env) app.command()(generate_ci.generate_ci_workflow)

if name == "main": app()
