#!/usr/bin/env python3
"""
Process all PDFs in parallel using multiprocessing for maximum CPU utilization
"""

import json
import os
from pathlib import Path
from multiprocessing import Pool, cpu_count
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


def process_single_pdf(pdf_path):
    """Process a single PDF - designed for parallel execution"""
    print(f"\n{'='*60}")
    print(f"[WORKER] Processing: {Path(pdf_path).name}")
    print('='*60)

    try:
        # Get metadata
        print(f"  [WORKER] Getting metadata...")
        metadata = get_pdf_metadata(pdf_path)

        if "error" in metadata:
            print(f"  [ERROR] {metadata['error']}")
            return {
                "file": pdf_path,
                "status": "failed",
                "error": metadata["error"]
            }

        print(f"  [WORKER] Pages: {metadata['page_count']}")
        print(f"  [WORKER] Size: {metadata['file_size_mb']} MB")

        # Get chunking strategy
        print(f"  [WORKER] Calculating optimal chunks...")
        chunk_info = get_smart_chunks(pdf_path, max_chars_per_chunk=100000)

        if "error" in chunk_info:
            print(f"  [ERROR] {chunk_info['error']}")
            return {
                "file": pdf_path,
                "status": "failed",
                "error": chunk_info["error"]
            }

        print(f"  [WORKER] Total chunks: {chunk_info['total_chunks']}")

        # Extract text
        print(f"  [WORKER] Extracting text...")
        full_text_parts = []

        for chunk in chunk_info['chunks']:
            chunk_result = extract_text_from_pages(
                pdf_path,
                chunk['start_page'],
                chunk['end_page']
            )

            if "error" in chunk_result:
                print(f"    [ERROR] Chunk {chunk['chunk_number']}: {chunk_result['error']}")
                continue

            full_text_parts.append(chunk_result['text'])
            print(f"    [WORKER] Chunk {chunk['chunk_number']}/{chunk_info['total_chunks']}: {chunk_result['text_length_chars']} chars")

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

        print(f"  [SUCCESS] {text_file}")
        print(f"  [WORKER] Total characters: {len(full_text):,}")

        return {
            "file": pdf_path,
            "status": "success",
            "pages": metadata['page_count'],
            "size_mb": metadata['file_size_mb'],
            "text_file": str(text_file),
            "metadata_file": str(metadata_file),
            "total_chars": len(full_text)
        }

    except Exception as e:
        print(f"  [ERROR] Unexpected error: {str(e)}")
        return {
            "file": pdf_path,
            "status": "failed",
            "error": str(e)
        }


if __name__ == "__main__":
    # Get number of CPUs
    num_cpus = cpu_count()
    num_workers = min(len(pdfs), num_cpus)  # Don't spawn more workers than PDFs

    print("="*60)
    print("PARALLEL PDF PROCESSOR")
    print("="*60)
    print(f"CPUs detected: {num_cpus}")
    print(f"PDFs to process: {len(pdfs)}")
    print(f"Parallel workers: {num_workers}")
    print("="*60)

    # Process PDFs in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_single_pdf, pdfs)

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
        f.write(f"**Processing used {num_workers} parallel workers**\n\n")
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

    print(f"\n[SUCCESS] Index created: {index_file}")
    print(f"[SUCCESS] Summary saved: {summary_file}")
    print(f"[SUCCESS] All extracted files saved to: {output_dir}")
    print(f"\nStats:")
    print(f"  - Successful: {successful}/{len(pdfs)}")
    print(f"  - Failed: {failed}/{len(pdfs)}")
    print(f"  - Total characters: {total_chars:,}")
