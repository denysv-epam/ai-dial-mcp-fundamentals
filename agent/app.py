import asyncio
import json
import os

from mcp_client import MCPClient
from dial_client import DialClient
from models.message import Message, Role
from prompts import SYSTEM_PROMPT

async def main():
    # 1. Create MCP client with docker_image
    async with MCPClient(docker_image="mcp/duckduckgo:latest") as mcp_client:
        
        # 2. Get Available MCP Tools
        print("\n=== Available Tools ===")
        tools: list[dict] = await mcp_client.get_tools()
        for tool in tools:
            print(json.dumps(tool, indent=2))
        
        # 3. Create DialClient
        api_key = os.getenv("DIAL_API_KEY")
        if not api_key:
            raise ValueError("DIAL_API_KEY environment variable is required")
        
        dial_client = DialClient(
            api_key=api_key,
            endpoint="https://ai-proxy.lab.epam.com",
            tools=tools,
            mcp_client=mcp_client,
        )
        
        # 4. Create list with messages and add SYSTEM_PROMPT
        messages: list[Message] = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]
        
        # 5. Create console chat
        print("\n=== DuckDuckGo Search Agent is ready! ===")
        print("Type your search query or 'exit' to quit.\n")
        
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            messages.append(Message(role=Role.USER, content=user_input))
            
            # Get AI response
            ai_message: Message = await dial_client.get_completion(messages)
            
            # Add AI message to history
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())