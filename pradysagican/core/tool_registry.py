"""
PRADYSAGICAN v2.0 - Unified Tool Registry
Supports direct Python functions, MCP servers, and API integrations
"""

import logging
import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolSchema:
    """Schema describing a tool's interface"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    return_type: str = "string"
    category: str = "general"
    enabled: bool = True
    
    def to_json(self) -> str:
        """Convert to JSON for LLM"""
        return json.dumps({
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'required': self.required_params,
        })


class Tool(ABC):
    """Base class for all tools"""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments"""
        pass
    
    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """Get tool schema for LLM"""
        pass


class PythonFunctionTool(Tool):
    """Wrapper for direct Python functions"""
    
    def __init__(self, func: Callable, description: str = None):
        self.func = func
        self.description = description or func.__doc__ or "No description"
        self.is_async = inspect.iscoroutinefunction(func)
    
    async def execute(self, **kwargs) -> Any:
        """Execute wrapped function"""
        if self.is_async:
            return await self.func(**kwargs)
        else:
            return await asyncio.to_thread(self.func, **kwargs)
    
    def get_schema(self) -> ToolSchema:
        """Extract schema from function signature"""
        sig = inspect.signature(self.func)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:
                continue
            
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
            
            parameters[param_name] = {
                'type': param_type,
                'description': f"Parameter: {param_name}"
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return ToolSchema(
            name=self.func.__name__,
            description=self.description,
            parameters=parameters,
            required_params=required,
            category="python"
        )


class MCPServerTool(Tool):
    """Tool that calls an MCP server"""
    
    def __init__(self, name: str, mcp_url: str, method: str, description: str = None):
        self.name = name
        self.mcp_url = mcp_url
        self.method = method
        self.description = description or f"MCP tool: {name}"
    
    async def execute(self, **kwargs) -> Any:
        """Execute MCP tool"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/tools/{self.method}",
                    json=kwargs,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get('result')
                else:
                    raise Exception(f"MCP error: {response.text}")
        except Exception as e:
            logger.error(f"MCP tool failed: {e}")
            raise
    
    def get_schema(self) -> ToolSchema:
        """Get MCP tool schema"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            category="mcp",
        )


class ToolRegistry:
    """Centralized registry for all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.by_category: Dict[str, List[str]] = {}
        self._init_builtin_tools()
    
    def _init_builtin_tools(self):
        """Initialize built-in tools"""
        
        # System tools
        self.register_function(
            name="system_info",
            func=self._system_info,
            description="Get system information"
        )
        
        self.register_function(
            name="list_files",
            func=self._list_files,
            description="List files in a directory"
        )
        
        self.register_function(
            name="read_file",
            func=self._read_file,
            description="Read a file's contents"
        )
        
        self.register_function(
            name="write_file",
            func=self._write_file,
            description="Write to a file"
        )
        
        logger.info(f"Initialized {len(self.tools)} built-in tools")
    
    def register_function(
        self,
        name: str,
        func: Callable,
        description: str = None,
        category: str = "general"
    ):
        """Register a Python function as a tool"""
        tool = PythonFunctionTool(func, description)
        schema = tool.get_schema()
        schema.name = name
        schema.category = category
        
        self.tools[name] = tool
        
        if category not in self.by_category:
            self.by_category[category] = []
        self.by_category[category].append(name)
        
        logger.debug(f"Registered tool: {name} ({category})")
    
    def register_mcp_server(
        self,
        name: str,
        mcp_url: str,
        description: str = None
    ):
        """Register an MCP server"""
        tool = MCPServerTool(name, mcp_url, name, description)
        self.tools[name] = tool
        
        category = "mcp"
        if category not in self.by_category:
            self.by_category[category] = []
        self.by_category[category].append(name)
        
        logger.debug(f"Registered MCP tool: {name} ({mcp_url})")
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        try:
            logger.debug(f"Executing tool: {tool_name} with args: {kwargs}")
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            raise
    
    def list_available_tools(self, category: Optional[str] = None) -> List[ToolSchema]:
        """List all available tools (optionally filtered by category)"""
        schemas = []
        
        for tool_name, tool in self.tools.items():
            schema = tool.get_schema()
            if category is None or schema.category == category:
                schemas.append(schema)
        
        return schemas
    
    def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """Get schema for a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].get_schema()
        return None
    
    # ===== BUILT-IN TOOL IMPLEMENTATIONS =====
    
    async def _system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import platform
        import psutil
        
        return {
            'platform': platform.system(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
        }
    
    async def _list_files(self, directory: str = ".") -> List[str]:
        """List files in a directory"""
        import os
        try:
            return os.listdir(directory)
        except Exception as e:
            raise ValueError(f"Cannot list directory {directory}: {e}")
    
    async def _read_file(self, filepath: str) -> str:
        """Read file contents"""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Cannot read file {filepath}: {e}")
    
    async def _write_file(self, filepath: str, content: str) -> str:
        """Write to a file"""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return f"File written: {filepath}"
        except Exception as e:
            raise ValueError(f"Cannot write to file {filepath}: {e}")


# Global tool registry
_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance
