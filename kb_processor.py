#!/usr/bin/env python3
"""
Automated KB Processor - Processes all PDFs sequentially through MCP
Memory-efficient: processes one PDF at a time, writes chunks immediately to disk
"""

import json
import time
from pathlib import Path
from server import get_pdf_metadata, extract_text_from_pages, get_smart_chunks

# Configuration
KB_DIR = Path(r"C:\KB\ModernEvasion")
OUTPUT_DIR = KB_DIR / "extracted"
CHUNK_SIZE = 30000  # Smaller chunks to avoid memory issues

def find_all_pdfs():
    """Find all PDF files in the KB directory"""
    return sorted(KB_DIR.glob("*.pdf"))

def process_all_pdfs():
    """Process all PDFs one at a time"""

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdfs = find_all_pdfs()

    if not pdfs:
        print("No PDFs found in", KB_DIR)
        return

    print("="*70)
    print(f"KNOWLEDGE BASE PROCESSOR - {len(pdfs)} PDFs to process")
    print("="*70)

    results = []
    start_time = time.time()

    for idx, pdf_path in enumerate(pdfs, 1):
        pdf_start = time.time()
        print(f"\n[{idx}/{len(pdfs)}] {pdf_path.name}")
        print("-"*70)

        result = {
            "file": str(pdf_path),
            "name": pdf_path.name,
            "status": "pending"
        }

        try:
            # 1. Get metadata
            print("  Analyzing PDF...", end=" ", flush=True)
            metadata = get_pdf_metadata(str(pdf_path))

            if "error" in metadata:
                print(f"FAILED: {metadata['error']}")
                result["status"] = "failed"
                result["error"] = metadata["error"]
                results.append(result)
                continue

            print(f"OK ({metadata['page_count']} pages, {metadata['file_size_mb']} MB)")
            result.update({
                "pages": metadata['page_count'],
                "size_mb": metadata['file_size_mb']
            })

            # 2. Calculate chunks
            print("  Planning extraction...", end=" ", flush=True)
            chunk_info = get_smart_chunks(str(pdf_path), max_chars_per_chunk=CHUNK_SIZE)

            if "error" in chunk_info:
                print(f"FAILED: {chunk_info['error']}")
                result["status"] = "failed"
                result["error"] = chunk_info["error"]
                results.append(result)
                continue

            print(f"OK ({chunk_info['total_chunks']} chunks)")

            # 3. Setup output files
            safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")
            text_file = OUTPUT_DIR / f"{safe_name}.txt"
            metadata_file = OUTPUT_DIR / f"{safe_name}_metadata.json"

            # Write header
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"# {pdf_path.name}\n")
                f.write(f"# Pages: {metadata['page_count']}\n")
                f.write(f"# Size: {metadata['file_size_mb']} MB\n")
                if metadata.get('title'):
                    f.write(f"# Title: {metadata['title']}\n")
                if metadata.get('author'):
                    f.write(f"# Author: {metadata['author']}\n")
                f.write("\n" + "="*80 + "\n\n")

            # 4. Extract text chunk by chunk
            print(f"  Extracting text ({chunk_info['total_chunks']} chunks):")
            total_chars = 0
            failed_chunks = 0

            for chunk in chunk_info['chunks']:
                chunk_result = extract_text_from_pages(
                    str(pdf_path),
                    chunk['start_page'],
                    chunk['end_page']
                )

                if "error" in chunk_result:
                    print(f"    Chunk {chunk['chunk_number']}: FAILED")
                    failed_chunks += 1
                    continue

                # Append to file immediately (memory-friendly)
                with open(text_file, 'a', encoding='utf-8') as f:
                    f.write(chunk_result['text'])
                    f.write("\n\n")

                chars = chunk_result['text_length_chars']
                total_chars += chars
                print(f"    Chunk {chunk['chunk_number']}/{chunk_info['total_chunks']}: {chars:,} chars")

                # Brief pause to avoid overwhelming system
                time.sleep(0.1)

            # 5. Save metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Record result
            pdf_time = time.time() - pdf_start
            result.update({
                "status": "success",
                "text_file": str(text_file),
                "metadata_file": str(metadata_file),
                "total_chars": total_chars,
                "failed_chunks": failed_chunks,
                "processing_time": round(pdf_time, 2)
            })

            print(f"  COMPLETE: {total_chars:,} chars extracted in {pdf_time:.1f}s")
            print(f"  Saved to: {text_file.name}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

        results.append(result)

        # Save progress after each PDF
        progress_file = OUTPUT_DIR / "processing_progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "completed": idx,
                "total": len(pdfs),
                "results": results
            }, f, indent=2)

    # Final summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    total_chars = sum(r.get("total_chars", 0) for r in results)

    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"Time: {total_time:.1f} seconds")
    print(f"Successful: {successful}/{len(pdfs)}")
    print(f"Failed: {failed}/{len(pdfs)}")
    print(f"Total characters extracted: {total_chars:,}")

    # Save final summary
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
    create_index(results)

    print(f"\nFiles saved to: {OUTPUT_DIR}")
    print(f"  - Index: INDEX.md")
    print(f"  - Summary: processing_summary.json")
    print(f"  - Text files: {successful} files")

def create_index(results):
    """Create a markdown index of all processed PDFs"""
    index_file = OUTPUT_DIR / "INDEX.md"

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# Knowledge Base - Extracted PDFs\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Documents\n\n")

        for result in results:
            name = result["name"]

            if result["status"] == "success":
                text_file = Path(result["text_file"]).name
                f.write(f"### ✅ {name}\n")
                f.write(f"- **Status:** Successfully extracted\n")
                f.write(f"- **Pages:** {result['pages']}\n")
                f.write(f"- **Size:** {result['size_mb']} MB\n")
                f.write(f"- **Characters:** {result['total_chars']:,}\n")
                f.write(f"- **Text File:** [{text_file}]({text_file})\n")
                f.write(f"- **Processing Time:** {result.get('processing_time', 'N/A')}s\n\n")
            else:
                f.write(f"### ❌ {name}\n")
                f.write(f"- **Status:** Failed\n")
                f.write(f"- **Error:** {result.get('error', 'Unknown error')}\n\n")

if __name__ == "__main__":
    try:
        process_all_pdfs()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")