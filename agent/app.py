import asyncio
import json
import os

from dial_client import DialClient
from mcp import Resource
from mcp.types import Prompt
from mcp_client import MCPClient
from models.message import Message, Role
from prompts import SYSTEM_PROMPT


async def main():
    """
    Main entry point for the User Management Agent.

    This agent connects to an MCP server to perform CRUD operations on users
    through natural language interactions.

    Prerequisites:
        1. Start the mock user service:
           $ docker compose up -d

        2. Start the MCP server (in separate terminal, from mcp_server dir):
           $ cd mcp_server
           $ python server.py

        3. Run this agent (from agent dir):
           $ cd agent
           $ python app.py

    Environment Variables:
        DIAL_API_KEY: Your DIAL API key for AI model access
    """

    async with MCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
        print("\n=== Available Resources ===")
        resources: list[Resource] = await mcp_client.get_resources()
        for resource in resources:
            print(resource)

        print("\n=== Available Tools ===")
        tools: list[dict] = await mcp_client.get_tools()
        for tool in tools:
            print(json.dumps(tool, indent=2))

        api_key = os.getenv("DIAL_API_KEY")
        if not api_key:
            raise ValueError("DIAL_API_KEY environment variable is required")
        
        dial_client = DialClient(
            api_key=api_key,
            endpoint="https://ai-proxy.lab.epam.com",
            tools=tools,
            mcp_client=mcp_client,
        )

        messages: list[Message] = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]

        print("\n=== Available Prompts ===")
        prompts: list[Prompt] = await mcp_client.get_prompts()
        for prompt in prompts:
            print(prompt)
            content = await mcp_client.get_prompt(prompt.name)
            print(content)
            messages.append(
                Message(
                    role=Role.USER,
                    content=f"## Prompt provided by MCP server:\n{prompt.description}\n{content}",
                )
            )

        print("MCP-based Agent is ready! Type your query or 'exit' to exit.")
        while True:
            user_input = input("\n> ").strip()
            if user_input.lower() == "exit":
                break

            messages.append(Message(role=Role.USER, content=user_input))

            ai_message: Message = await dial_client.get_completion(messages)
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
