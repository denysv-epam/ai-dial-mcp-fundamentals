from typing import Optional, Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent, Resource, Prompt


class MCPClient:
    """Handles MCP server connection and tool execution via stdio"""

    def __init__(self, docker_image: str) -> None:
        self.docker_image = docker_image
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        self._process = None

    async def __aenter__(self) -> "MCPClient":
        # 1. Create StdioServerParameters
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "--rm", "-i", self.docker_image]
        )
        
        # 2. Init _stdio_context
        self._stdio_context = stdio_client(server_params)
        
        # 3. Create read_stream, write_stream
        read_stream, write_stream = await self._stdio_context.__aenter__()
        
        # 4. Create ClientSession
        self._session_context = ClientSession(read_stream, write_stream)
        
        # 5. Init session
        self.session = await self._session_context.__aenter__()
        
        # 6. Initialize and print result
        print("Initializing MCP session...")
        init_result = await self.session.initialize()
        print(f"Capabilities: {init_result.model_dump_json(indent=2)}")

        # 7. Return self
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Shutdown session context if present
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        
        # Shutdown stdio context if present
        if self._stdio_context:
            await self._stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        # 1. Call list_tools
        tools = await self.session.list_tools()
        
        # 2. Return formatted list
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        print(f"    🔧 Calling `{tool_name}` with {tool_args}")
        
        # 1. Call tool
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        
        # 2. Get content at index 0
        content = tool_result.content[0]
        
        # 3. Print result
        print(f"    ⚙️: {content}\n")
        
        # 4. Return text or content
        if isinstance(content, TextContent):
            return content.text
        
        return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        
        try:
            result = await self.session.list_resources()
            return result.resources
        except Exception as e:
            print(f"Server doesn't support list_resources: {e}")
            return []

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            result = await self.session.list_prompts()
            return result.prompts
        except Exception as e:
            print(f"Server doesn't support list_prompts: {e}")
            return []
