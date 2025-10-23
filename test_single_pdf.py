#!/usr/bin/env python3
"""Test processing a single PDF"""

from pathlib import Path
from server import get_pdf_metadata, extract_text_from_pages, get_smart_chunks

# Test with smallest PDF first
pdf_path = r"C:\KB\ModernEvasion\Evasion_Course_Slides.pdf"

print(f"Testing with: {pdf_path}")
print("="*60)

# Step 1: Get metadata
print("\n1. Getting metadata...")
metadata = get_pdf_metadata(pdf_path)
print(f"   Result: {metadata}")

if "error" in metadata:
    print(f"ERROR: {metadata['error']}")
    exit(1)

print(f"   Pages: {metadata['page_count']}")
print(f"   Size: {metadata['file_size_mb']} MB")

# Step 2: Get first 5 pages of text
print("\n2. Extracting first 5 pages...")
result = extract_text_from_pages(pdf_path, 1, 5, max_chars=10000)

if "error" in result:
    print(f"ERROR: {result['error']}")
    exit(1)

print(f"   Extracted {result['text_length_chars']} characters")
print(f"\n   Preview (first 500 chars):")
print(f"   {result['text'][:500]}")

print("\n" + "="*60)
print("SUCCESS! Basic extraction works.")
print("="*60)
