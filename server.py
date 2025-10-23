#!/usr/bin/env python3
"""
PDF MCP Server - Handles large PDF files with chunking and intelligent extraction
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pypdf
import pdfplumber
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server


app = Server("pdf-processor")


def get_pdf_metadata(pdf_path: str) -> dict[str, Any]:
    """Extract metadata from a PDF file."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"error": f"File not found: {pdf_path}"}

        file_size = path.stat().st_size

        with pypdf.PdfReader(pdf_path) as reader:
            metadata = {
                "file_path": str(path.absolute()),
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "page_count": len(reader.pages),
                "is_encrypted": reader.is_encrypted,
            }

            # Add PDF metadata if available
            if reader.metadata:
                metadata["title"] = reader.metadata.get("/Title", "")
                metadata["author"] = reader.metadata.get("/Author", "")
                metadata["subject"] = reader.metadata.get("/Subject", "")
                metadata["creator"] = reader.metadata.get("/Creator", "")

            return metadata
    except Exception as e:
        return {"error": f"Failed to read PDF metadata: {str(e)}"}


def extract_text_from_pages(pdf_path: str, start_page: int = 1, end_page: int | None = None, max_chars: int | None = None) -> dict[str, Any]:
    """Extract text from a range of pages in a PDF."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"error": f"File not found: {pdf_path}"}

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Validate page range
            if start_page < 1 or start_page > total_pages:
                return {"error": f"Invalid start_page: {start_page}. PDF has {total_pages} pages."}

            if end_page is None:
                end_page = total_pages
            elif end_page > total_pages:
                end_page = total_pages

            # Extract text
            extracted_text = []
            total_chars = 0
            pages_processed = 0
            truncated = False

            for page_num in range(start_page - 1, end_page):
                page = pdf.pages[page_num]
                page_text = page.extract_text() or ""

                # Check if we would exceed max_chars
                if max_chars and (total_chars + len(page_text)) > max_chars:
                    # Add partial text from this page
                    remaining_chars = max_chars - total_chars
                    extracted_text.append(f"--- Page {page_num + 1} (partial) ---\n{page_text[:remaining_chars]}")
                    total_chars += remaining_chars
                    pages_processed += 1
                    truncated = True
                    break

                extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                total_chars += len(page_text)
                pages_processed += 1

            result = {
                "pdf_path": str(path.absolute()),
                "total_pages": total_pages,
                "pages_requested": f"{start_page}-{end_page}",
                "pages_processed": pages_processed,
                "text_length_chars": total_chars,
                "text": "\n\n".join(extracted_text)
            }

            if truncated:
                result["truncated"] = True
                result["note"] = f"Text truncated at {max_chars} characters. Use smaller page ranges or increase max_chars."

            return result

    except Exception as e:
        return {"error": f"Failed to extract text: {str(e)}"}


def search_pdf(pdf_path: str, query: str, context_chars: int = 200, max_results: int = 50) -> dict[str, Any]:
    """Search for text within a PDF and return matches with context."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"error": f"File not found: {pdf_path}"}

        results = []
        query_lower = query.lower()

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                page_text_lower = page_text.lower()

                # Find all occurrences
                start_idx = 0
                while True:
                    idx = page_text_lower.find(query_lower, start_idx)
                    if idx == -1:
                        break

                    # Extract context around match
                    context_start = max(0, idx - context_chars)
                    context_end = min(len(page_text), idx + len(query) + context_chars)
                    context = page_text[context_start:context_end]

                    # Add ellipsis if truncated
                    if context_start > 0:
                        context = "..." + context
                    if context_end < len(page_text):
                        context = context + "..."

                    results.append({
                        "page": page_num,
                        "context": context,
                        "position": idx
                    })

                    if len(results) >= max_results:
                        break

                    start_idx = idx + 1

                if len(results) >= max_results:
                    break

        return {
            "pdf_path": str(path.absolute()),
            "query": query,
            "total_matches": len(results),
            "matches": results,
            "truncated": len(results) >= max_results
        }

    except Exception as e:
        return {"error": f"Failed to search PDF: {str(e)}"}


def get_smart_chunks(pdf_path: str, max_chars_per_chunk: int = 50000, overlap_pages: int = 1) -> dict[str, Any]:
    """Get information about how to chunk a large PDF for processing."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"error": f"File not found: {pdf_path}"}

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Calculate chunks
            chunks = []
            current_page = 1
            chunk_num = 1

            while current_page <= total_pages:
                # Estimate how many pages fit in chunk
                test_chars = 0
                end_page = current_page

                for page_num in range(current_page - 1, total_pages):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text() or ""

                    if test_chars + len(page_text) > max_chars_per_chunk and end_page > current_page:
                        break

                    test_chars += len(page_text)
                    end_page = page_num + 1

                chunks.append({
                    "chunk_number": chunk_num,
                    "start_page": current_page,
                    "end_page": end_page,
                    "estimated_chars": test_chars
                })

                # Move to next chunk with overlap
                current_page = end_page + 1 - overlap_pages
                if current_page <= end_page - overlap_pages:
                    current_page = end_page + 1
                chunk_num += 1

            return {
                "pdf_path": str(path.absolute()),
                "total_pages": total_pages,
                "max_chars_per_chunk": max_chars_per_chunk,
                "overlap_pages": overlap_pages,
                "total_chunks": len(chunks),
                "chunks": chunks
            }

    except Exception as e:
        return {"error": f"Failed to calculate chunks: {str(e)}"}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available PDF processing tools."""
    return [
        Tool(
            name="pdf_get_metadata",
            description="Get metadata about a PDF file including page count, file size, title, author, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Full path to the PDF file"
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="pdf_extract_text",
            description="Extract text from a specific range of pages in a PDF. Useful for processing large PDFs in chunks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Full path to the PDF file"
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Starting page number (1-indexed)",
                        "default": 1
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Ending page number (inclusive). If not specified, extracts to the end."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to extract. If exceeded, extraction stops and truncated=true is returned."
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="pdf_search",
            description="Search for text within a PDF and return all matches with surrounding context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Full path to the PDF file"
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search for (case-insensitive)"
                    },
                    "context_chars": {
                        "type": "integer",
                        "description": "Number of characters to include before/after each match for context",
                        "default": 200
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 50
                    }
                },
                "required": ["pdf_path", "query"]
            }
        ),
        Tool(
            name="pdf_get_chunks",
            description="Calculate optimal chunk ranges for processing a large PDF. Returns page ranges that fit within character limits.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Full path to the PDF file"
                    },
                    "max_chars_per_chunk": {
                        "type": "integer",
                        "description": "Target maximum characters per chunk",
                        "default": 50000
                    },
                    "overlap_pages": {
                        "type": "integer",
                        "description": "Number of pages to overlap between chunks (helps maintain context)",
                        "default": 1
                    }
                },
                "required": ["pdf_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "pdf_get_metadata":
        result = get_pdf_metadata(arguments["pdf_path"])
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "pdf_extract_text":
        result = extract_text_from_pages(
            arguments["pdf_path"],
            arguments.get("start_page", 1),
            arguments.get("end_page"),
            arguments.get("max_chars")
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "pdf_search":
        result = search_pdf(
            arguments["pdf_path"],
            arguments["query"],
            arguments.get("context_chars", 200),
            arguments.get("max_results", 50)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "pdf_get_chunks":
        result = get_smart_chunks(
            arguments["pdf_path"],
            arguments.get("max_chars_per_chunk", 50000),
            arguments.get("overlap_pages", 1)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
