#!/usr/bin/env python3
"""
Process a SINGLE PDF file - easy on system resources
Usage: python process_single.py <pdf_path>
"""

import json
import sys
from pathlib import Path
from server import get_pdf_metadata, extract_text_from_pages, get_smart_chunks

def process_pdf(pdf_path, output_dir=None):
    """Process a single PDF file with minimal resource usage"""

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return False

    # Default output directory
    if output_dir is None:
        output_dir = Path(r"C:\KB\ModernEvasion\extracted")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print(f"Processing: {pdf_path.name}")
    print("="*70)

    try:
        # Step 1: Get metadata (lightweight)
        print("[1/4] Reading metadata...", end=" ", flush=True)
        metadata = get_pdf_metadata(str(pdf_path))

        if "error" in metadata:
            print(f"FAILED: {metadata['error']}")
            return False

        print(f"OK")
        print(f"      Pages: {metadata['page_count']}")
        print(f"      Size: {metadata['file_size_mb']} MB")

        # Step 2: Calculate chunks (lightweight)
        print("[2/4] Planning extraction...", end=" ", flush=True)
        # Use smaller chunks to be memory-friendly
        chunk_info = get_smart_chunks(str(pdf_path), max_chars_per_chunk=50000)

        if "error" in chunk_info:
            print(f"FAILED: {chunk_info['error']}")
            return False

        print(f"OK ({chunk_info['total_chunks']} chunks)")

        # Step 3: Extract text chunk by chunk (memory-friendly)
        print(f"[3/4] Extracting text from {chunk_info['total_chunks']} chunks...")

        # Create safe filename
        safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")
        text_file = output_dir / f"{safe_name}.txt"

        # Write header
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"# {pdf_path.name}\n")
            f.write(f"# Extracted from: {pdf_path}\n")
            f.write(f"# Pages: {metadata['page_count']}\n")
            f.write(f"# Size: {metadata['file_size_mb']} MB\n")
            if metadata.get('title'):
                f.write(f"# Title: {metadata['title']}\n")
            if metadata.get('author'):
                f.write(f"# Author: {metadata['author']}\n")
            f.write("\n" + "="*80 + "\n\n")

        # Process chunks one at a time (memory-friendly)
        total_chars = 0
        for chunk in chunk_info['chunks']:
            print(f"      Chunk {chunk['chunk_number']}/{chunk_info['total_chunks']}...", end=" ", flush=True)

            chunk_result = extract_text_from_pages(
                str(pdf_path),
                chunk['start_page'],
                chunk['end_page']
            )

            if "error" in chunk_result:
                print(f"FAILED: {chunk_result['error']}")
                continue

            # Append to file (memory-friendly)
            with open(text_file, 'a', encoding='utf-8') as f:
                f.write(chunk_result['text'])
                f.write("\n\n")

            chars = chunk_result['text_length_chars']
            total_chars += chars
            print(f"OK ({chars:,} chars)")

        # Step 4: Save metadata
        print("[4/4] Saving metadata...", end=" ", flush=True)
        metadata_file = output_dir / f"{safe_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print("OK")

        print("\n" + "="*70)
        print("SUCCESS!")
        print(f"  Text saved to: {text_file.name}")
        print(f"  Total characters: {total_chars:,}")
        print(f"  Metadata saved to: {metadata_file.name}")
        print("="*70)

        return True

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python process_single.py <pdf_path> [output_dir]")
        print("\nAvailable PDFs in C:\\KB\\ModernEvasion:")
        kb_dir = Path(r"C:\KB\ModernEvasion")
        if kb_dir.exists():
            pdfs = list(kb_dir.glob("*.pdf"))
            for i, pdf in enumerate(pdfs, 1):
                size = pdf.stat().st_size / (1024*1024)
                print(f"  {i}. {pdf.name} ({size:.1f} MB)")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    success = process_pdf(pdf_path, output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()