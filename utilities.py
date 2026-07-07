import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

DOTENV_FILE = ".env"
DOTENV_TEMPLATE = "env.example"

load_dotenv(dotenv_path=DOTENV_FILE)

def _create_dotenv():
    dotenv_path = Path.cwd() / DOTENV_FILE
    template_path = Path.cwd() / DOTENV_TEMPLATE
    if not dotenv_path.is_file():
        shutil.copy(template_path, dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)

def get_config(key: str, default: str) -> str:
    _create_dotenv()
    return os.getenv(key, default)

class ToolResponse(BaseModel):
    status: str
    message: str
    data: str
