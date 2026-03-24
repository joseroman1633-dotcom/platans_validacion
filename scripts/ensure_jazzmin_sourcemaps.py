from pathlib import Path

THEMES = [
    "cerulean",
    "cosmo",
    "cyborg",
    "darkly",
    "default",
    "flatly",
    "journal",
    "litera",
    "lumen",
    "lux",
    "materia",
    "minty",
    "morph",
    "pulse",
    "quartz",
    "sandstone",
    "simplex",
    "sketchy",
    "slate",
    "solar",
    "spacelab",
    "superhero",
    "united",
    "vapor",
    "yeti",
    "zephyr",
]

base_dir = Path(__file__).resolve().parent.parent
vendor_dir = base_dir / "static" / "vendor" / "bootswatch"

for theme in THEMES:
    sourcemap_file = vendor_dir / theme / "bootstrap.min.css.map"
    sourcemap_file.parent.mkdir(parents=True, exist_ok=True)
    if not sourcemap_file.exists():
        sourcemap_file.write_text("{}\n", encoding="utf-8")
        print(f"Created {sourcemap_file}")
