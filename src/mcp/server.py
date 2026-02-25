"""
MCP server implementation for the Todo AI Chatbot application.
"""
from mcp.server import Server
from mcp.types import Notification, Result, Request
import asyncio
import logging
from typing import Dict, Any, List

# Initialize the MCP server
server = Server("todo-chatbot-mcp")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_server(host: str = "localhost", port: int = 8001):
    """Run the MCP server."""
    logger.info(f"Starting MCP Server on {host}:{port}")
    async with server.serve_socket_strict(host, port):
        logger.info("MCP Server running...")
        # Keep the server running
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    # Run the server if this file is executed directly
    asyncio.run(run_server())