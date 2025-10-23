# PDF MCP Server

A Model Context Protocol (MCP) server for processing large PDF files with intelligent chunking and text extraction.

## Features

- **PDF Metadata**: Get file info, page count, author, title, etc.
- **Text Extraction**: Extract text from specific page ranges with character limits
- **PDF Search**: Search within PDFs with contextual results
- **Smart Chunking**: Calculate optimal page ranges for processing large PDFs

## Tools

### 1. `pdf_get_metadata`
Get metadata about a PDF file.

**Parameters:**
- `pdf_path` (string, required): Full path to the PDF file

**Returns:**
- File size, page count, title, author, and other metadata

### 2. `pdf_extract_text`
Extract text from a range of pages.

**Parameters:**
- `pdf_path` (string, required): Full path to the PDF file
- `start_page` (integer, optional): Starting page (1-indexed, default: 1)
- `end_page` (integer, optional): Ending page (default: last page)
- `max_chars` (integer, optional): Maximum characters to extract

**Returns:**
- Extracted text with page markers
- Character count and truncation info

### 3. `pdf_search`
Search for text within a PDF.

**Parameters:**
- `pdf_path` (string, required): Full path to the PDF file
- `query` (string, required): Text to search for (case-insensitive)
- `context_chars` (integer, optional): Context characters around matches (default: 200)
- `max_results` (integer, optional): Maximum results (default: 50)

**Returns:**
- List of matches with page numbers and context

### 4. `pdf_get_chunks`
Calculate optimal chunking strategy for large PDFs.

**Parameters:**
- `pdf_path` (string, required): Full path to the PDF file
- `max_chars_per_chunk` (integer, optional): Target chunk size (default: 50000)
- `overlap_pages` (integer, optional): Page overlap between chunks (default: 1)

**Returns:**
- List of chunks with page ranges and estimated character counts

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure in Claude Code (see Configuration section)

## Configuration

Add to your Claude Code MCP settings (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "pdf-processor": {
      "command": "python",
      "args": ["c:\\Users\\Will\\pdf-mcp-server\\server.py"]
    }
  }
}
```

After configuration, restart Claude Code to load the MCP server.

## Usage Examples

### Processing a 55MB PDF

1. First, get metadata:
```
Use pdf_get_metadata to check the page count
```

2. Calculate chunks:
```
Use pdf_get_chunks to determine optimal page ranges
```

3. Extract text by chunk:
```
Use pdf_extract_text with the page ranges from step 2
```

4. Search across the PDF:
```
Use pdf_search to find specific content
```

## Technical Details

- Uses `pdfplumber` for high-quality text extraction
- Uses `pypdf` for metadata and PDF structure
- Runs locally using your compute resources
- No file size limits (processes in chunks)
- Handles encrypted PDFs (if not password-protected)

## Troubleshooting

**Server not appearing in Claude Code:**
- Check that the path in config is correct
- Restart Claude Code after configuration changes
- Check Python is accessible from command line

**Extraction issues:**
- Scanned PDFs may have poor text extraction (OCR not yet implemented)
- Some PDFs may have unusual encoding
