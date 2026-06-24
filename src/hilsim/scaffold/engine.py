from pathlib import Path
from jinja2 import Environment, PackageLoader

def scaffold_project(project_name: str) -> None: 
    """Create the scaffolding for a project in the current directory"""
    root = Path.cwd() / project_name
    root.mkdir(parents=False, exist_ok=False)

    env = Environment(loader=PackageLoader("hilsim", "scaffold/templates"), keep_trailing_newline=True)
    context = {"project_name": project_name}
    manifest  = {
        "main.py.jinja": "main.py",
        "sensor_config.toml.jinja": "sensor_config.toml",
        "device_config.toml.jinja": "device_config.toml",
        "actuator_config.toml.jinja": "actuator_config.toml",
        "world_state.toml.jinja": "world_state.toml",
        "sensors/sensor_template.py.jinja": "sensors/sensor_template.py",
        "actuators/actuator_template.py.jinja": "actuators/actuator_template.py"
    }

    for template_path, output_path in manifest.items():
        template = env.get_template(template_path)
        rendered = template.render(**context)
        out = root / output_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
