import click
from hilsim.scaffold.engine import scaffold_project

@click.group()
def cli():
    """hilsim: hardware-in-the-loop simulation framework"""
    pass

@cli.command()
@click.argument("project_name")
def create(project_name): 
    """Scaffold a new hilsim project in the current directory"""
    click.echo(f"Creating project '{project_name}'...")
    try: 
        scaffold_project(project_name)
        click.echo(f"Project '{project_name}' created successfully")
    except FileExistsError:
        """Note: engine won't create a project that already exists
        (i.e. has the same name)"""
        click.echo(f"Error: directory '{project_name}' already exists", err=True)