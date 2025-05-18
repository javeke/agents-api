from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

templates_path = Path(__file__).parent.parent / "templates"

env = Environment(
  loader=FileSystemLoader(templates_path),
  autoescape=select_autoescape(["html", "xml"])
)

def render_template(template_name: str, context: dict) -> str:
  template = env.get_template(template_name)
  return template.render(**context)
