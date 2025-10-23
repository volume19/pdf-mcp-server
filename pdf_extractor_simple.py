#!/usr/bin/env python3
"""
SIMPLE PDF EXTRACTOR - Based on proven PyMuPDF approach
No complex chunking, just page-by-page extraction with memory management
"""

import fitz  # PyMuPDF
import gc
import json
from pathlib import Path
import time

KB_DIR = Path(r"C:\KB\ModernEvasion")
OUTPUT_DIR = KB_DIR / "extracted"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf_simple(pdf_path):
    """Extract text from PDF using PyMuPDF - simple and reliable"""
    pdf_path = Path(pdf_path)
    safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")

    print(f"\nProcessing: {pdf_path.name}")
    print("-" * 70)

    try:
        # Open PDF with PyMuPDF
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        file_size_mb = round(pdf_path.stat().st_size / (1024*1024), 2)

        print(f"  Pages: {total_pages}")
        print(f"  Size: {file_size_mb} MB")

        # Output files
        text_file = OUTPUT_DIR / f"{safe_name}.txt"
        metadata_file = OUTPUT_DIR / f"{safe_name}_metadata.json"

        # Extract metadata
        metadata = {
            "file": str(pdf_path),
            "pages": total_pages,
            "size_mb": file_size_mb,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", "")
        }

        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # Write header to text file
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"# {pdf_path.name}\n")
            f.write(f"# Pages: {total_pages}\n")
            f.write(f"# Size: {file_size_mb} MB\n")
            if metadata["title"]:
                f.write(f"# Title: {metadata['title']}\n")
            if metadata["author"]:
                f.write(f"# Author: {metadata['author']}\n")
            f.write("\n" + "="*80 + "\n\n")

        # Extract text page by page (memory efficient)
        total_chars = 0
        print(f"  Extracting text from {total_pages} pages...")

        for page_num in range(total_pages):
            # Get page
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Write to file immediately (don't keep in memory)
            with open(text_file, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Page {page_num + 1} ---\n")
                f.write(text)

            total_chars += len(text)

            # Progress indicator every 10 pages
            if (page_num + 1) % 10 == 0:
                print(f"    Processed {page_num + 1}/{total_pages} pages ({total_chars:,} chars so far)")

            # Clean up page object
            page = None

            # Force garbage collection every 50 pages
            if (page_num + 1) % 50 == 0:
                gc.collect()

        # Close document
        doc.close()
        doc = None
        gc.collect()

        print(f"  SUCCESS! Extracted {total_chars:,} total characters")
        print(f"  Saved to: {text_file.name}")

        return {
            "status": "success",
            "file": str(pdf_path),
            "pages": total_pages,
            "size_mb": file_size_mb,
            "total_chars": total_chars,
            "text_file": str(text_file),
            "metadata_file": str(metadata_file)
        }

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return {
            "status": "failed",
            "file": str(pdf_path),
            "error": str(e)
        }


def process_all_pdfs():
    """Process all PDFs in the KB directory"""
    pdfs = sorted(KB_DIR.glob("*.pdf"))

    if not pdfs:
        print("No PDFs found in", KB_DIR)
        return

    print("="*70)
    print(f"SIMPLE PDF EXTRACTOR - {len(pdfs)} PDFs to process")
    print("="*70)

    results = []
    successful = 0
    failed = 0
    total_chars = 0
    start_time = time.time()

    for idx, pdf_path in enumerate(pdfs, 1):
        print(f"\n[{idx}/{len(pdfs)}]", end="")
        result = extract_pdf_simple(pdf_path)
        results.append(result)

        if result["status"] == "success":
            successful += 1
            total_chars += result["total_chars"]
        else:
            failed += 1

    # Save summary
    total_time = time.time() - start_time
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_pdfs": len(pdfs),
        "successful": successful,
        "failed": failed,
        "total_chars": total_chars,
        "total_time": round(total_time, 2),
        "results": results
    }

    summary_file = OUTPUT_DIR / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # Create index
    index_file = OUTPUT_DIR / "INDEX.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# Knowledge Base - Extracted PDFs\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- **Total PDFs:** {len(pdfs)}\n")
        f.write(f"- **Successful:** {successful}\n")
        f.write(f"- **Failed:** {failed}\n")
        f.write(f"- **Total Characters:** {total_chars:,}\n")
        f.write(f"- **Processing Time:** {total_time:.1f} seconds\n\n")
        f.write("## Documents\n\n")

        for result in results:
            if result["status"] == "success":
                text_file = Path(result["text_file"]).name
                f.write(f"### ✅ {Path(result['file']).name}\n")
                f.write(f"- **Pages:** {result['pages']}\n")
                f.write(f"- **Size:** {result['size_mb']} MB\n")
                f.write(f"- **Characters:** {result['total_chars']:,}\n")
                f.write(f"- **Text File:** [{text_file}]({text_file})\n\n")
            else:
                f.write(f"### ❌ {Path(result['file']).name}\n")
                f.write(f"- **Error:** {result.get('error', 'Unknown error')}\n\n")

    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"Time: {total_time:.1f} seconds")
    print(f"Successful: {successful}/{len(pdfs)}")
    print(f"Failed: {failed}/{len(pdfs)}")
    print(f"Total characters: {total_chars:,}")
    print(f"\nFiles saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_all_pdfs()