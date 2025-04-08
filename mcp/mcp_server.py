import argparse

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

mcp = FastMCP("String Manipulation Plugin", "1.0.0")

@mcp.tool()
async def reverse(input:str) -> str:
    """reverse the input string"""
    return input[::-1]

async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server 
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    sse = SseServerTransport("/messages/")
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    uvicorn.run(starlette_app, host=args.host, port=args.port)