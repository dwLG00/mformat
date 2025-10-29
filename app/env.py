import pexpect
import inspect
import platform
from typing import get_type_hints, Any, Union, get_origin, get_args
from pydantic import BaseModel
import os

class SandboxEnvironment:
    def __init__(self, download_dir: str, archive_dir: str):
        self.download_dir = download_dir
        self.archive_dir = archive_dir
        self.on_linux = (platform.system() == "Linux")
        cmd = (
            f"bwrap "
            f"--unshare-pid --unshare-uts --unshare-ipc --unshare-net "
            f"--dev-bind /dev /dev "
            f"--ro-bind /usr /usr "
            f"--ro-bind /bin /bin "
            f"--ro-bind /lib /lib "
            f"--ro-bind /lib64 /lib64 "
            f"--ro-bind /etc /etc "
            f"--tmpfs /tmp "
            f"--bind {self.download_dir} /download "
            f"--bind {self.archive_dir} /archive "
            f"--chdir /download "
            f"/bin/bash --noprofile --norc -i"
        )
        env = os.environ.copy()
        env.setdefault("TERM", "dumb")  # avoids many readline escapes
        self.shell = pexpect.spawn(cmd, encoding="utf-8", env=env)

        self.tools = {
            'pwd': self.pwd,
            'ls': self.ls,
            'cd': self.cd,
            'convert': self.convert,
            'unar': self.unar,
            'cp': self.cp,
            'mv': self.mv
        }

        self.prompt = "__SBX__$ "
        self.shell.sendline(f'export PS1="{self.prompt}"')
        self.shell.expect_exact(self.prompt)
        self.shell.sendline("bind 'set enable-bracketed-paste off' || true")
        self.shell.expect_exact(self.prompt)

    def _run(self, line: str):
        self.shell.sendline(line)
        self.shell.expect_exact(self.prompt)
        return self.shell.before.replace("\r\n", "\n").rstrip("\n")

    def pwd(self) -> str:
        "Return working directory name"
        return self._run("pwd")
    
    def ls(self, dir: str = None) -> str:
        "Return contents of given directory (default: working directory)"
        if dir:
            return self._run(f"ls -lagh {dir}")
        return self._run("ls -lagh")
    
    def cd(self, dir: str) -> str:
        "Change working directory to given directory"
        return self._run(f"cd {dir}")
    
    def convert(self, string: str) -> str:
        """Convert between image formats as well as resize an image, blur, crop, despeckle, dither, draw on, flip, join, re-sample, and much more.
        This is equivalent to running the imagemagick convert command `convert {string}`.

        Example: `convert("my-directory/my-directory-*.jpeg ./my-directory.pdf")` aliases to `convert my-directory/my-directory-*.jpeg ./my-directory.pdf`
        """
        return self._run(f"convert {string}")
    
    def unar(self, filename: str) -> str:
        "Extracts given tarball"
        return self._run(f"unar {filename}")
    
    def cp(self, string: str) -> str:
        """Copies files/directories to another location.
        This is equivalent to running `cp {string}`.
        """
        return self._run(f"cp {string}")
    
    def mv(self, string: str) -> str:
        """Moves files/directories to another location.
        This is equivalent to running `mv {string}`.
        """
        return self._run(f"mv {string}")
    
    def run_tool(self, tool_name: str, tool_args: dict) -> str:
        tool_func = self.tools.get(tool_name)
        if not tool_func:
            raise ValueError(f"Got tool call for `{tool_name}`, but not present in list of tools")
        
        response = tool_func(**tool_args)
        return str(response)

    def as_tools(self) -> list:
        '''Return list of "tools" for openai API'''
        def function_to_signature(func):
            sig = inspect.signature(func)
            hints = get_type_hints(func)
        
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                param_type = hints.get(param_name, str)
                properties[param_name] = recursive_schema(param_type)
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            return {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
        
        return [function_to_signature(func) for func in self.tools.values()]

        
def recursive_schema(param_type: Any) -> dict:    
    # handle basic types
    if param_type == int:
        return {"type": "integer"}
    elif param_type == float:
        return {"type": "number"}
    elif param_type == bool:
        return {"type": "boolean"}
    elif param_type == str:
        return {"type": "string"}
    
    # handle pydantic models
    try:
        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            schema = param_type.model_json_schema()
            if 'title' in schema:
                del schema['title']
            return schema
    except TypeError:
        pass
    
    origin = get_origin(param_type)
    args = get_args(param_type)
    
    if origin is list:
        item_type = args[0] if args else str
        return {
            "type": "array",
            "items":recursive_schema(item_type)
        }
    
    elif origin is dict:
        value_type = args[1] if len(args) > 1 else str
        return {
            "type": "object",
            "additionalProperties": recursive_schema(value_type)
        }
    
    elif origin is Union:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return recursive_schema(non_none_args[0])
        else:
            return {
                "anyOf": [recursive_schema(arg) for arg in non_none_args]
            }
    
    return {"type": "string"}