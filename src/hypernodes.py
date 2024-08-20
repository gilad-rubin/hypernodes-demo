import sys
import inspect
from pathlib import Path
import json
import importlib
from typing import Union, Any, Dict, List, Optional, Callable
from pathlib import Path
from hamilton.driver import Builder, Driver
import hypster
import importlib
import inspect
import logging

class HyperNode:
    def __init__(
        self,
        name: str,
        dag_modules: List[str],
        hp_config: Callable,
    ):
        self.name = name
        self.dag_modules = dag_modules
        self.hp_config = hp_config
        self._instantiated_inputs: Optional[Dict[str, Any]] = None
        self._driver: Optional[Driver] = None

    @property
    def instantiated_inputs(self) -> Optional[Dict[str, Any]]:
        return self._instantiated_inputs

    @property
    def driver(self) -> Optional[Driver]:
        return self._driver

    def save(self, folder: str):
        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)

        # Save DAG modules
        dag_module_paths = []
        for i, module in enumerate(self.dag_modules):
            if i == 0:
                module_path = folder_path / f"{self.name}_dag.py"
            else:
                module_path = folder_path / f"{self.name}_dag_{i+1}.py"
            with open(module_path, 'w') as f:
                f.write(inspect.getsource(module))
            dag_module_paths.append(str(module_path.relative_to(folder_path)))

        # Save hp_config
        hp_config_path = None
        if self.hp_config:
            hp_config_path = folder_path / f"{self.name}_hp_config.py"
            hypster.save(self.hp_config, str(hp_config_path))
            hp_config_path = str(hp_config_path.relative_to(folder_path))

        # Save HyperNode metadata
        metadata = {
            "name": self.name,
            "dag_module_paths": dag_module_paths,
            "hp_config_path": hp_config_path
        }
        metadata_path = folder_path / f"{self.name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

    @staticmethod
    def load(folder: str):
        folder_path = Path(folder)
        
        # Load metadata
        metadata_path = next(folder_path.glob("*_metadata.json"))
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load DAG modules
        dag_modules = []
        for module_path in metadata['dag_module_paths']:
            full_path = folder_path / module_path
            module_name = full_path.stem
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.__name__ = module_name
            sys.modules[module_name] = module
            dag_modules.append(module)
        
        # Load hp_config
        hp_config = None
        if metadata['hp_config_path']:
            hp_config_path = folder_path / metadata['hp_config_path']
            hp_config = hypster.load(str(hp_config_path))
        
        return HyperNode(metadata['name'], dag_modules, hp_config)
    
    def instantiate_inputs(self, selections: Dict[str, Any] = {}, overrides: Dict[str, Any] = {}, return_config_snapshot=False) -> None:
        if return_config_snapshot: #TODO: fix this :)
            self._instantiated_inputs, snapshot = self.hp_config(selections=selections, overrides=overrides, return_config_snapshot=True)
            self._instantiated_inputs.update(snapshot)
        else:
            self._instantiated_inputs = self.hp_config(selections=selections, overrides=overrides, return_config_snapshot=False)

    def init_driver(self) -> None:
        if self._instantiated_inputs is None:
            raise ValueError("You must instantiate inputs before initializing the driver")
        
        builder = self._instantiated_inputs.get("builder", Builder())
        
        try:
            self._driver = builder.with_modules(*self.dag_modules).build()
        except Exception as e:
            logging.error(f"Failed to build driver: {e}")
            raise RuntimeError(f"Failed to build driver: {e}")

    def ensure_driver_initialized(self) -> None:
        if self._driver is None:
            try:
                self.init_driver()
            except Exception as e:
                logging.error(f"Failed to initialize driver: {e}")
                raise RuntimeError(f"Failed to initialize driver: {e}")
            
    def execute(self, final_vars: List[Any] = [], inputs: Dict[str, Any] = {}) -> Dict[str, Any]:
        self.ensure_driver_initialized()
        
        if self._driver is None:
            raise RuntimeError("Driver initialization failed")
        
        #TODO: remove this in the future:
        inputs = inputs.copy()
        {k:inputs.pop(k) for k in self._driver.config}
        
        return self._driver.execute(final_vars=final_vars, inputs=inputs)
    
    def get_node_inputs(self, node_name: str) -> Dict[str, Any]:
        self.ensure_driver_initialized()
        
        if self._driver is None:
            raise RuntimeError("Driver initialization failed")
        
        upstream_args = get_upstream_args(self._driver, node_name)
        return self.execute(final_vars=upstream_args, inputs=self._instantiated_inputs)

def get_func_arg_list(func: Callable) -> List[str]:
    import inspect
    return inspect.getfullargspec(func).args

def get_upstream_args(driver: Driver, node_name: str) -> List[str]:
    func = driver.graph.nodes[node_name].callable
    upstream_args = get_func_arg_list(func)
    return [arg for arg in upstream_args if not arg.startswith(node_name)]