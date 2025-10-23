#!/usr/bin/env python3
"""
Process all PDFs in C:\KB\ModernEvasion and create searchable text extracts
"""

import json
import os
from pathlib import Path
from server import get_pdf_metadata, extract_text_from_pages, get_smart_chunks

# PDF files to process
pdfs = [
    r"C:\KB\ModernEvasion\OffensiveDriverDevelopment.pdf",
    r"C:\KB\ModernEvasion\watermarked_WKL_ODPC_Lab_Guide_v1.2.3_unlocked.pdf",
    r"C:\KB\ModernEvasion\Evasion_Course_Slides.pdf",
    r"C:\KB\ModernEvasion\EvasiveMalware.pdf",
    r"C:\KB\ModernEvasion\WindowsSecurityInternals.pdf",
    r"C:\KB\ModernEvasion\ArtCyberWarfare.pdf",
    r"C:\KB\ModernEvasion\EvadingEDR.pdf",
    r"C:\KB\ModernEvasion\BOF Development and Tradecraft (1).pdf",
]

# Output directory
output_dir = Path(r"C:\KB\ModernEvasion\extracted")
output_dir.mkdir(exist_ok=True)

# Process each PDF
results = []

for pdf_path in pdfs:
    print(f"\n{'='*60}")
    print(f"Processing: {Path(pdf_path).name}")
    print('='*60)

    # Get metadata
    print("  Getting metadata...")
    metadata = get_pdf_metadata(pdf_path)

    if "error" in metadata:
        print(f"  ERROR: {metadata['error']}")
        results.append({
            "file": pdf_path,
            "status": "failed",
            "error": metadata["error"]
        })
        continue

    print(f"  Pages: {metadata['page_count']}")
    print(f"  Size: {metadata['file_size_mb']} MB")

    # Get chunking strategy
    print("  Calculating optimal chunks...")
    chunk_info = get_smart_chunks(pdf_path, max_chars_per_chunk=100000)

    if "error" in chunk_info:
        print(f"  ERROR: {chunk_info['error']}")
        results.append({
            "file": pdf_path,
            "status": "failed",
            "error": chunk_info["error"]
        })
        continue

    print(f"  Total chunks: {chunk_info['total_chunks']}")

    # Extract text
    print("  Extracting text...")
    full_text_parts = []

    for chunk in chunk_info['chunks']:
        chunk_result = extract_text_from_pages(
            pdf_path,
            chunk['start_page'],
            chunk['end_page']
        )

        if "error" in chunk_result:
            print(f"    Chunk {chunk['chunk_number']} ERROR: {chunk_result['error']}")
            continue

        full_text_parts.append(chunk_result['text'])
        print(f"    Chunk {chunk['chunk_number']}/{chunk_info['total_chunks']}: {chunk_result['text_length_chars']} chars")

    # Combine all text
    full_text = "\n\n".join(full_text_parts)

    # Create safe filename
    safe_name = Path(pdf_path).stem.replace(" ", "_").replace("(", "").replace(")", "")

    # Save extracted text
    text_file = output_dir / f"{safe_name}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"# {Path(pdf_path).name}\n")
        f.write(f"# Extracted from: {pdf_path}\n")
        f.write(f"# Pages: {metadata['page_count']}\n")
        f.write(f"# Size: {metadata['file_size_mb']} MB\n")
        if metadata.get('title'):
            f.write(f"# Title: {metadata['title']}\n")
        if metadata.get('author'):
            f.write(f"# Author: {metadata['author']}\n")
        f.write("\n" + "="*80 + "\n\n")
        f.write(full_text)

    # Save metadata
    metadata_file = output_dir / f"{safe_name}_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"  SAVED: {text_file}")
    print(f"  Total characters: {len(full_text):,}")

    results.append({
        "file": pdf_path,
        "status": "success",
        "pages": metadata['page_count'],
        "size_mb": metadata['file_size_mb'],
        "text_file": str(text_file),
        "metadata_file": str(metadata_file),
        "total_chars": len(full_text)
    })

# Create summary
print(f"\n\n{'='*60}")
print("PROCESSING COMPLETE")
print('='*60)

summary_file = output_dir / "processing_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

# Create index
print("\nCreating searchable index...")
index_file = output_dir / "INDEX.md"
with open(index_file, 'w', encoding='utf-8') as f:
    f.write("# Modern Evasion Knowledge Base - Extracted PDFs\n\n")
    f.write(f"Processed {len(pdfs)} PDFs from C:\\KB\\ModernEvasion\n\n")
    f.write("## Available Documents\n\n")

    for result in results:
        if result['status'] == 'success':
            name = Path(result['file']).name
            text_file = Path(result['text_file']).name
            f.write(f"### {name}\n")
            f.write(f"- **Pages:** {result['pages']}\n")
            f.write(f"- **Size:** {result['size_mb']} MB\n")
            f.write(f"- **Extracted Text:** [{text_file}]({text_file})\n")
            f.write(f"- **Characters:** {result['total_chars']:,}\n\n")
        else:
            name = Path(result['file']).name
            f.write(f"### {name} (FAILED)\n")
            f.write(f"- **Error:** {result['error']}\n\n")

print(f"Index created: {index_file}")
print(f"Summary saved: {summary_file}")
print(f"\nAll extracted files saved to: {output_dir}")
