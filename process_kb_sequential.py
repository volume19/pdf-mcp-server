#!/usr/bin/env python3
"""
Process all PDFs sequentially (faster and more reliable than parallel for I/O bound tasks)
"""

import json
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

results = []

print("="*70)
print("PDF EXTRACTION - PROCESSING ALL KNOWLEDGE BASE PDFS")
print("="*70)
print(f"Total PDFs: {len(pdfs)}")
print("="*70)

for idx, pdf_path in enumerate(pdfs, 1):
    print(f"\n[{idx}/{len(pdfs)}] {Path(pdf_path).name}")
    print("-"*70)

    try:
        # Get metadata
        print("  [1/4] Reading metadata...", end=" ", flush=True)
        metadata = get_pdf_metadata(pdf_path)

        if "error" in metadata:
            print(f"FAILED")
            print(f"        Error: {metadata['error']}")
            results.append({"file": pdf_path, "status": "failed", "error": metadata["error"]})
            continue

        print(f"OK ({metadata['page_count']} pages, {metadata['file_size_mb']} MB)")

        # Get chunking strategy
        print("  [2/4] Calculating chunks...", end=" ", flush=True)
        chunk_info = get_smart_chunks(pdf_path, max_chars_per_chunk=100000)

        if "error" in chunk_info:
            print(f"FAILED")
            print(f"        Error: {chunk_info['error']}")
            results.append({"file": pdf_path, "status": "failed", "error": chunk_info["error"]})
            continue

        print(f"OK ({chunk_info['total_chunks']} chunks)")

        # Extract text
        print(f"  [3/4] Extracting text...", flush=True)
        full_text_parts = []

        for chunk in chunk_info['chunks']:
            chunk_result = extract_text_from_pages(
                pdf_path,
                chunk['start_page'],
                chunk['end_page']
            )

            if "error" in chunk_result:
                print(f"        Chunk {chunk['chunk_number']}: FAILED - {chunk_result['error']}")
                continue

            full_text_parts.append(chunk_result['text'])
            print(f"        Chunk {chunk['chunk_number']}/{chunk_info['total_chunks']}: {chunk_result['text_length_chars']:,} chars")

        # Combine and save
        print("  [4/4] Saving...", end=" ", flush=True)
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

        print(f"OK ({len(full_text):,} chars)")
        print(f"        Saved to: {text_file.name}")

        results.append({
            "file": pdf_path,
            "status": "success",
            "pages": metadata['page_count'],
            "size_mb": metadata['file_size_mb'],
            "text_file": str(text_file),
            "metadata_file": str(metadata_file),
            "total_chars": len(full_text)
        })

    except Exception as e:
        print(f"FAILED")
        print(f"        Unexpected error: {str(e)}")
        results.append({"file": pdf_path, "status": "failed", "error": str(e)})

# Create summary
print(f"\n\n{'='*70}")
print("PROCESSING COMPLETE")
print('='*70)

summary_file = output_dir / "processing_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

# Create index
index_file = output_dir / "INDEX.md"
with open(index_file, 'w', encoding='utf-8') as f:
    f.write("# Modern Evasion Knowledge Base - Extracted PDFs\n\n")
    f.write(f"Processed {len(pdfs)} PDFs from C:\\KB\\ModernEvasion\n\n")
    f.write("## Available Documents\n\n")

    successful = 0
    failed = 0
    total_chars = 0

    for result in results:
        if result['status'] == 'success':
            successful += 1
            name = Path(result['file']).name
            text_file = Path(result['text_file']).name
            total_chars += result['total_chars']
            f.write(f"### {name}\n")
            f.write(f"- **Pages:** {result['pages']}\n")
            f.write(f"- **Size:** {result['size_mb']} MB\n")
            f.write(f"- **Extracted Text:** [{text_file}]({text_file})\n")
            f.write(f"- **Characters:** {result['total_chars']:,}\n\n")
        else:
            failed += 1
            name = Path(result['file']).name
            f.write(f"### {name} (FAILED)\n")
            f.write(f"- **Error:** {result['error']}\n\n")

    f.write("\n## Summary\n\n")
    f.write(f"- **Successful:** {successful}/{len(pdfs)}\n")
    f.write(f"- **Failed:** {failed}/{len(pdfs)}\n")
    f.write(f"- **Total characters extracted:** {total_chars:,}\n")

print(f"\nResults:")
print(f"  Successful: {successful}/{len(pdfs)}")
print(f"  Failed: {failed}/{len(pdfs)}")
print(f"  Total characters: {total_chars:,}")
print(f"\nFiles saved to: {output_dir}")
print(f"  - Index: INDEX.md")
print(f"  - Summary: processing_summary.json")
print(f"  - Text files: {successful} .txt files")
print(f"  - Metadata: {successful} _metadata.json files")
