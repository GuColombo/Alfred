import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import importlib.util
import sys
from loguru import logger

from config.settings import ConfigManager

@dataclass
class PluginManifest:
    """Plugin manifest definition."""
    name: str
    version: str
    description: str
    entry_point: str
    permissions: List[str]
    dependencies: List[str]
    enabled: bool = True

class PluginExecutor:
    """Executes plugins in a controlled environment."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.plugin_dir = Path(config.get("plugins.plugin_dir", "./tools/plugins"))
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        self.timeout = config.get("plugins.sandbox_timeout", 300)
        self.allowed_domains = config.get("plugins.allowed_domains", ["localhost"])
        
        # Plugin registry
        self.plugins: Dict[str, PluginManifest] = {}
        self.plugin_modules: Dict[str, Any] = {}
        
        # Load existing plugins
        self._load_plugins()
        
        logger.info(f"Plugin executor initialized with {len(self.plugins)} plugins")
    
    def _load_plugins(self):
        """Load all plugins from the plugin directory."""
        try:
            for plugin_path in self.plugin_dir.iterdir():
                if plugin_path.is_dir() and (plugin_path / "manifest.json").exists():
                    self._load_plugin(plugin_path)
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")
    
    def _load_plugin(self, plugin_path: Path):
        """Load a single plugin."""
        try:
            manifest_file = plugin_path / "manifest.json"
            with open(manifest_file, 'r') as f:
                manifest_data = json.load(f)
            
            manifest = PluginManifest(**manifest_data)
            self.plugins[manifest.name] = manifest
            
            # Load plugin module if enabled
            if manifest.enabled:
                self._load_plugin_module(plugin_path, manifest)
            
            logger.debug(f"Loaded plugin: {manifest.name}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}")
    
    def _load_plugin_module(self, plugin_path: Path, manifest: PluginManifest):
        """Load plugin Python module."""
        try:
            entry_file = plugin_path / manifest.entry_point
            if not entry_file.exists():
                logger.error(f"Plugin entry point not found: {entry_file}")
                return
            
            spec = importlib.util.spec_from_file_location(
                f"plugin_{manifest.name}",
                entry_file
            )
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules for imports
            sys.modules[f"plugin_{manifest.name}"] = module
            spec.loader.exec_module(module)
            
            self.plugin_modules[manifest.name] = module
            logger.debug(f"Loaded plugin module: {manifest.name}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin module {manifest.name}: {e}")
    
    def list_plugins(self) -> Dict[str, bool]:
        """List all plugins and their enabled status."""
        return {name: manifest.enabled for name, manifest in self.plugins.items()}
    
    def list_available_plugins(self) -> List[str]:
        """List names of available (enabled) plugins."""
        return [name for name, manifest in self.plugins.items() if manifest.enabled]
    
    def toggle_plugin(self, name: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        try:
            if name not in self.plugins:
                logger.error(f"Plugin not found: {name}")
                return False
            
            manifest = self.plugins[name]
            manifest.enabled = enabled
            
            # Update manifest file
            plugin_path = self.plugin_dir / name
            manifest_file = plugin_path / "manifest.json"
            
            with open(manifest_file, 'w') as f:
                json.dump(manifest.__dict__, f, indent=2)
            
            # Load/unload module
            if enabled and name not in self.plugin_modules:
                self._load_plugin_module(plugin_path, manifest)
            elif not enabled and name in self.plugin_modules:
                del self.plugin_modules[name]
            
            logger.info(f"Plugin {name} {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to toggle plugin {name}: {e}")
            return False
    
    def install_plugin(self, source_path: str) -> bool:
        """Install a plugin from a source path."""
        try:
            source = Path(source_path)
            
            if not source.exists():
                logger.error(f"Plugin source not found: {source_path}")
                return False
            
            # Read manifest
            manifest_file = source / "manifest.json"
            if not manifest_file.exists():
                logger.error(f"Plugin manifest not found: {manifest_file}")
                return False
            
            with open(manifest_file, 'r') as f:
                manifest_data = json.load(f)
            
            manifest = PluginManifest(**manifest_data)
            
            # Check if plugin already exists
            if manifest.name in self.plugins:
                logger.warning(f"Plugin {manifest.name} already exists, updating...")
            
            # Copy plugin to plugin directory
            target_path = self.plugin_dir / manifest.name
            if target_path.exists():
                import shutil
                shutil.rmtree(target_path)
            
            import shutil
            shutil.copytree(source, target_path)
            
            # Load the plugin
            self._load_plugin(target_path)
            
            logger.info(f"Plugin {manifest.name} installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin from {source_path}: {e}")
            return False
    
    def execute_plugin(self, name: str, method: str, **kwargs) -> Any:
        """Execute a specific plugin method."""
        try:
            if name not in self.plugins:
                raise ValueError(f"Plugin not found: {name}")
            
            if not self.plugins[name].enabled:
                raise ValueError(f"Plugin not enabled: {name}")
            
            if name not in self.plugin_modules:
                raise ValueError(f"Plugin module not loaded: {name}")
            
            module = self.plugin_modules[name]
            
            if not hasattr(module, method):
                raise ValueError(f"Method {method} not found in plugin {name}")
            
            # Execute with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Plugin execution timed out after {self.timeout}s")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            try:
                method_func = getattr(module, method)
                result = method_func(**kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
        except Exception as e:
            logger.error(f"Plugin execution failed {name}.{method}: {e}")
            raise
    
    def execute_from_response(self, response: str) -> Optional[str]:
        """Execute plugins based on LLM response content."""
        try:
            # Simple pattern matching for tool execution
            # This would be enhanced with more sophisticated parsing
            
            lines = response.split('\n')
            results = []
            
            for line in lines:
                line = line.strip()
                
                # Look for execution patterns
                if line.startswith('execute:'):
                    command = line[8:].strip()
                    result = self._execute_shell_command(command)
                    results.append(f"Command: {command}\nOutput: {result}")
                
                elif line.startswith('search:'):
                    query = line[7:].strip()
                    result = self._execute_web_search(query)
                    results.append(f"Search: {query}\nResults: {result}")
                
                elif line.startswith('tool:'):
                    tool_call = line[5:].strip()
                    result = self._execute_tool_call(tool_call)
                    results.append(f"Tool: {tool_call}\nResult: {result}")
            
            return '\n\n'.join(results) if results else None
            
        except Exception as e:
            logger.error(f"Failed to execute from response: {e}")
            return f"Execution error: {e}"
    
    def _execute_shell_command(self, command: str) -> str:
        """Execute a shell command safely."""
        try:
            # Basic command sanitization
            if any(dangerous in command for dangerous in ['rm -rf', 'sudo', 'passwd', 'del /f']):
                return "Error: Dangerous command blocked"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tempfile.gettempdir()
            )
            
            if result.returncode == 0:
                return result.stdout or "Command executed successfully"
            else:
                return f"Error (code {result.returncode}): {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {e}"
    
    def _execute_web_search(self, query: str) -> str:
        """Execute a web search (placeholder)."""
        # This would integrate with a web search plugin
        return f"Web search for '{query}' would be executed here"
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Execute a generic tool call."""
        try:
            # Parse tool call (format: plugin_name.method_name(args))
            if '.' not in tool_call or '(' not in tool_call:
                return "Error: Invalid tool call format"
            
            plugin_name, method_part = tool_call.split('.', 1)
            method_name = method_part.split('(')[0]
            
            # Simple argument parsing (would be enhanced)
            args = {}
            if '(' in method_part and ')' in method_part:
                args_str = method_part.split('(')[1].split(')')[0]
                # Parse simple key=value arguments
                for arg in args_str.split(','):
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        args[key.strip()] = value.strip().strip('"\'')
            
            result = self.execute_plugin(plugin_name, method_name, **args)
            return str(result)
            
        except Exception as e:
            return f"Tool execution error: {e}"
    
    def get_status(self) -> str:
        """Get plugin executor status."""
        enabled_count = sum(1 for manifest in self.plugins.values() if manifest.enabled)
        return f"Plugins: {enabled_count}/{len(self.plugins)} enabled"
    
    def create_sample_plugins(self):
        """Create sample plugins for testing."""
        # Create a simple calculator plugin
        calc_plugin_dir = self.plugin_dir / "calculator"
        calc_plugin_dir.mkdir(exist_ok=True)
        
        # Manifest
        manifest = {
            "name": "calculator",
            "version": "1.0.0",
            "description": "Basic calculator plugin",
            "entry_point": "calculator.py",
            "permissions": ["compute"],
            "dependencies": [],
            "enabled": True
        }
        
        with open(calc_plugin_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Plugin code
        plugin_code = '''
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return float(a) + float(b)

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return float(a) * float(b)

def calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    # Simple and safe evaluation
    try:
        # Only allow basic math operations
        allowed_chars = set('0123456789+-*/.() ')
        if all(c in allowed_chars for c in expression):
            return eval(expression)
        else:
            raise ValueError("Invalid characters in expression")
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
'''
        
        with open(calc_plugin_dir / "calculator.py", 'w') as f:
            f.write(plugin_code)
        
        # Reload plugins
        self._load_plugins()
        
        logger.info("Sample calculator plugin created")