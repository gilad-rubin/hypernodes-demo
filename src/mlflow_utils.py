import mlflow

class HyperNodeMLFlow(mlflow.pyfunc.PythonModel):
    def __init__(self, node, final_vars, overrides={}):
        self.node = node
        self.final_vars = [final_vars] if isinstance(final_vars, str) else final_vars
        self.overrides = overrides
        self.context_loaded = False
        
    def load_context(self, context):
        #TODO: loadenv
        
        overrides = self.overrides.copy()
        for k, v in context.artifacts.items():
            overrides[k] = v
        
        self.node.instantiate_inputs(overrides=overrides)
        self.context_loaded = True
        
    def predict(self, context, model_input, params=None):
        if not self.context_loaded:
            self.load_context(context)
            
        inputs = self.node._instantiated_inputs
        dynamic_inputs = model_input.to_dict(orient="records")[0]
        inputs.update(dynamic_inputs)
        
        results = self.node.execute(final_vars=self.final_vars, inputs=inputs)
        
        if len(self.final_vars) == 1:
            results = results[self.final_vars[0]]
        
        return results
    
    
import os
import sys
from typing import List, Dict, Optional
import yaml

class EnvironmentGenerator:
    def __init__(self, 
                 env_name: str,
                 python_version: Optional[str] = None, 
                 dependency_file: Optional[str] = None,
                 extra_dependencies: Optional[List[str]] = None):
        self.env_name = env_name
        self.python_version = python_version or self._detect_python_version()
        self.dependency_file = dependency_file
        self.extra_dependencies = extra_dependencies or []
        self.dependencies: List[str] = []
        
        self._load_dependencies()

    def _detect_python_version(self) -> str:
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _load_dependencies(self):
        if self.dependency_file:
            self._parse_dependency_file()
        self.dependencies.extend(self.extra_dependencies)

    def _parse_dependency_file(self):
        if not os.path.exists(self.dependency_file):
            raise FileNotFoundError(f"Dependency file not found: {self.dependency_file}")
        
        # Simple parsing for requirements.txt
        # TODO: Add support for pyproject.toml and setup.py
        with open(self.dependency_file, 'r') as f:
            self.dependencies.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))

    def get_conda_environment_dict(self) -> Dict:
        return {
            "name": self.env_name,
            "channels": ["defaults"],
            "dependencies": [
                f"python={self.python_version}",
                "pip",
                {"pip": self.dependencies}
            ]
        }

    def get_pip_requirements_list(self) -> List[str]:
        return self.dependencies.copy()

    def export_conda_yaml(self, filepath: str = "environment.yml"):
        conda_env = self.get_conda_environment_dict()
        with open(filepath, 'w') as f:
            yaml.dump(conda_env, f, default_flow_style=False)

    def export_pip_requirements(self, filepath: str = "requirements.txt"):
        with open(filepath, 'w') as f:
            f.write("\n".join(self.get_pip_requirements_list()))

import os
import glob

def find_files_with_suffix(directory, suffix):
    pattern = os.path.join(directory, f"**/*{suffix}")
    return glob.glob(pattern, recursive=True)

def get_code_paths(folders=["src"], suffix=".py"):
    all_paths = []
    for folder in folders:
        folder_path = os.path.abspath(folder)
        paths = find_files_with_suffix(folder_path, suffix)
        all_paths.extend(paths)
    return all_paths