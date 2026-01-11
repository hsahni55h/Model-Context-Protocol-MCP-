"""
langchain_mcp_client_wconfig_openai.py

This file implements a LangChain MCP client that:
  - Loads configuration from a JSON file specified by the CONFIG environment variable.
  - Connects to one or more MCP servers defined in the config.
  - Loads available MCP tools from each connected server.
  - Uses the OpenAI API (via LangChain) to create a React agent with access to all tools.
  - Runs an interactive chat loop where user queries are processed by the agent.

Detailed explanations:
  - Retries (max_retries=2): If an API call fails due to transient issues (e.g., timeouts),
    it will retry up to 2 times.
  - Temperature (set to 0): A value of 0 means fully deterministic output; increase this
    for more creative responses.
  - Environment Variable: CONFIG should point to a config JSON that defines all MCP servers.
"""

import asyncio                        # For asynchronous operations
import os                             # To access environment variables and file paths
import sys                            # For system-specific parameters and error handling
import json                           # For reading and writing JSON data
from contextlib import AsyncExitStack # For managing multiple asynchronous context managers

# ---------------------------
# MCP Client Imports
# ---------------------------
from mcp import ClientSession, StdioServerParameters  # For managing MCP client sessions and server parameters
from mcp.client.stdio import stdio_client             # For establishing a stdio connection to an MCP server

# ---------------------------
# Agent and LLM Imports
# ---------------------------
from langchain_mcp_adapters.tools import load_mcp_tools  # Adapter to convert MCP tools to LangChain compatible tools
from langgraph.prebuilt import create_react_agent        # Function to create a prebuilt React agent using LangGraph
from langchain_openai import ChatOpenAI                  # Wrapper for the OpenAI API via LangChain

# ---------------------------
# Environment Setup
# ---------------------------
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from a .env file (e.g., OPENAI_API_KEY)

# ---------------------------
# Custom JSON Encoder for LangChain objects
# ---------------------------
class CustomEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle non-serializable objects returned by LangChain.

    If the object has a 'content' attribute (such as HumanMessage or ToolMessage),
    serialize it accordingly so the output can be printed as JSON.
    """
    def default(self, o):
        # Check if the object has a 'content' attribute
        if hasattr(o, "content"):
            # Return a dictionary containing the type and content of the object
            return {"type": o.__class__.__name__, "content": o.content}

        # Otherwise, use the default JSON serialization
        return super().default(o)

# ---------------------------
# Function: read_config_json
# ---------------------------
def read_config_json():
    """
    Reads the MCP server configuration JSON.

    Priority:
      1. Try to read the path from the CONFIG environment variable.
      2. If not set, fallback to a default file 'config.json' in the same directory.

    Returns:
        dict: Parsed JSON content with MCP server definitions.
    """

    # Attempt to get the config file path from the environment variable
    config_path = os.getenv("CONFIG")

    if not config_path:
        # If environment variable is not set, use a default config file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")

        print(f"⚠️ CONFIG not set. Falling back to: {config_path}")

    try:
        # Open and read the JSON config file
        with open(config_path, "r") as f:
            return json.load(f)

    except Exception as e:
        # If reading fails, print an error and exit the program
        print(f"❌ Failed to read config file at '{config_path}': {e}")
        sys.exit(1)

# ---------------------------
# OpenAI LLM Instantiation
# ---------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",                
    temperature=0,                      # 0 = deterministic responses
    max_retries=2,                      # Retry API calls up to 2 times for transient errors
    api_key=os.getenv("OPENAI_API_KEY") # OpenAI API key loaded from environment variables
)

# ---------------------------
# Main Function: run_agent
# ---------------------------
async def run_agent():
    """
    Connects to all MCP servers defined in the configuration, loads their tools,
    creates a unified React agent, and starts an interactive loop to query the agent.

    Steps:
      1. Read MCP server configuration from JSON.
      2. Connect to each MCP server over stdio.
      3. Initialize an MCP session for each server.
      4. Load available tools using the MCP → LangChain adapter.
      5. Aggregate tools from all servers into a single list.
      6. Create a React agent using OpenAI + the aggregated tools.
      7. Start an interactive chat loop for user queries.
    """

    # Load MCP server configuration from JSON file
    config = read_config_json()

    # Extract MCP server definitions from config
    mcp_servers = config.get("mcpServers", {})

    if not mcp_servers:
        print("❌ No MCP servers found in the configuration.")
        return

    tools = []  # This will store all tools from all connected MCP servers

    # AsyncExitStack helps manage multiple async resources cleanly
    async with AsyncExitStack() as stack:

        # Iterate over each MCP server defined in the configuration
        for server_name, server_info in mcp_servers.items():
            print(f"\n🔗 Connecting to MCP Server: {server_name}...")

            # Create StdioServerParameters using the command and arguments
            server_params = StdioServerParameters(
                command=server_info["command"],
                args=server_info["args"]
            )

            try:
                # Establish a stdio connection to the MCP server
                read, write = await stack.enter_async_context(stdio_client(server_params))

                # Create a client session using the stdio streams
                session = await stack.enter_async_context(ClientSession(read, write))

                # Initialize the MCP session (handshake / setup)
                await session.initialize()

                # Load MCP tools and convert them into LangChain tools
                server_tools = await load_mcp_tools(session)

                # Add each tool to the global tools list
                for tool in server_tools:
                    print(f"\n🔧 Loaded tool: {tool.name}")
                    tools.append(tool)

                print(f"\n✅ {len(server_tools)} tools loaded from {server_name}.")

            except Exception as e:
                # Handle connection or tool-loading errors
                print(f"❌ Failed to connect to server {server_name}: {e}")

        # If no tools were loaded, exit the program
        if not tools:
            print("❌ No tools loaded from any server. Exiting.")
            return

        # Create a React agent using OpenAI and the aggregated MCP tools
        agent = create_react_agent(llm, tools)

        # Start interactive chat loop
        print("\n🚀 MCP Client Ready! Type 'quit' to exit.")

        while True:
            # Read user input
            query = input("\nQuery: ").strip()

            if query.lower() == "quit":
                # Exit the loop if the user types 'quit'
                break

            # Invoke the agent asynchronously with the user query
            response = await agent.ainvoke({"messages": query})

            # Print the agent's response as formatted JSON
            print("\nResponse:")
            try:
                formatted = json.dumps(response, indent=2, cls=CustomEncoder)
                print(formatted)
            except Exception:
                # Fallback to raw string output if JSON serialization fails
                print(str(response))

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    # Run the asynchronous run_agent function using asyncio
    asyncio.run(run_agent())
