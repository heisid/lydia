import os
import shutil

from dotenv import load_dotenv
from pathlib import Path

DOTENV_FILE = ".env"
DOTENV_TEMPLATE = "env.example"

load_dotenv(dotenv_path=DOTENV_FILE)

def _create_dotenv():
    dotenv_path = Path.cwd() / DOTENV_FILE
    template_path = Path.cwd() / DOTENV_TEMPLATE
    if not dotenv_path.is_file():
        shutil.copy(template_path, dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)

def get_config(key: str) -> str | None:
    _create_dotenv()
    return os.getenv(key)