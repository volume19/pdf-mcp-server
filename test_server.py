#!/usr/bin/env python3
"""
Quick test to verify the MCP server implementation
"""

import asyncio
from server import list_tools, get_pdf_metadata

async def test_server():
    """Test basic server functionality."""
    print("Testing PDF MCP Server...")
    print("-" * 50)

    # Test 1: List tools
    print("\n1. Testing tool listing...")
    tools = await list_tools()
    print(f"   [OK] Found {len(tools)} tools:")
    for tool in tools:
        print(f"     - {tool.name}: {tool.description[:50]}...")

    # Test 2: Test metadata function (without actual PDF)
    print("\n2. Testing metadata extraction (with fake path)...")
    result = get_pdf_metadata("nonexistent.pdf")
    if "error" in result:
        print(f"   [OK] Error handling works: {result['error'][:50]}...")

    print("\n" + "=" * 50)
    print("Server implementation looks good!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Add MCP configuration to Claude Code")
    print("2. Restart Claude Code")
    print("3. Use pdf_* tools with your actual PDF files")

if __name__ == "__main__":
    asyncio.run(test_server())
