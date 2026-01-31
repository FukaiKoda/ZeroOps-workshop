import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

def load_module_from_path(module_name: str, file_path: Path) -> Optional[ModuleType]:
    """
    Dynamically loads a Python module from a given file path.
    """
    if not file_path.exists():
        return None

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Error loading module {module_name} from {file_path}: {e}")
        return None
    return None
