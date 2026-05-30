"""
loaders.py — Demonstrates all 5 ragstack loaders.

Each loader shows:
  - DocumentInfo  (file metadata)
  - First DocumentBlock (content + metadata)

Set PDF_FILE and EXCEL_FILE to your own files, or leave them as None to skip.
"""
from pathlib import Path

from ragstack_core.loaders import TextLoader, MarkdownLoader, CsvLoader, PdfLoader, ExcelLoader

SAMPLE_TXT = Path(__file__).parent / "sample_data" / "sample.txt"
SAMPLE_MD = Path(__file__).parent / "sample_data" / "sample.md"
SAMPLE_CSV = Path(__file__).parent / "sample_data" / "sample.csv"

# Set these to your own files, or leave as None to skip
TEXT_FILE = SAMPLE_TXT  # e.g. Path("/path/to/your.txt")
PDF_FILE = None          # e.g. Path("/path/to/your.pdf")
EXCEL_FILE = None        # e.g. Path("/path/to/your.xlsx")


def _separator(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def demo_text_loader() -> None:
    _separator("TextLoader — sample.txt")
    if TEXT_FILE is None:
        print("  Skipped — set TEXT_FILE at the top of this file to a .txt path")
        return
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(TEXT_FILE)
    print("DocumentInfo:")
    print(f"  id        : {info.document_id}")
    print(f"  name      : {info.file_name}")
    print(f"  type      : {info.file_type}")
    print(f"  size      : {info.file_size_bytes} bytes")

    blocks = loader.load_blocks(TEXT_FILE, info)
    first = next(iter(blocks))
    print("\nFirst DocumentBlock:")
    print(f"  block_index : {first.block_index}")
    print(f"  text preview: {first.text[:200]!r}")
    print(f"  metadata    : {first.metadata}")


def demo_markdown_loader() -> None:
    _separator("MarkdownLoader — sample.md")
    loader = MarkdownLoader()
    info = loader.load_info(SAMPLE_MD)
    print(f"DocumentInfo: name={info.file_name}, type={info.file_type}, size={info.file_size_bytes}B")

    blocks = list(loader.load_blocks(SAMPLE_MD, info))
    print(f"\nTotal blocks (one per heading): {len(blocks)}")
    for block in blocks:
        print(f"  block {block.block_index}: {block.text[:80]!r}")


def demo_csv_loader() -> None:
    _separator("CsvLoader — sample.csv")
    loader = CsvLoader(rows_per_block=5)
    info = loader.load_info(SAMPLE_CSV)
    print(f"DocumentInfo: name={info.file_name}, type={info.file_type}")

    blocks = list(loader.load_blocks(SAMPLE_CSV, info))
    print(f"\nTotal blocks: {len(blocks)}")
    first = blocks[0]
    print(f"First block text:\n{first.text}")
    print(f"Metadata: {first.metadata}")


def demo_pdf_loader() -> None:
    _separator("PdfLoader")
    if PDF_FILE is None:
        print("  Skipped — set PDF_FILE at the top of this file to a .pdf path")
        return
    loader = PdfLoader(pages_per_block=1)
    info = loader.load_info(PDF_FILE)
    print(f"DocumentInfo: name={info.file_name}")
    blocks = loader.load_blocks(PDF_FILE, info)
    first = next(iter(blocks))
    print(f"First block: {first.text[:200]!r}")
    print(f"Metadata: {first.metadata}")


def demo_excel_loader() -> None:
    _separator("ExcelLoader")
    if EXCEL_FILE is None:
        print("  Skipped — set EXCEL_FILE at the top of this file to a .xlsx path")
        return
    loader = ExcelLoader(rows_per_block=100)
    info = loader.load_info(EXCEL_FILE)
    print(f"DocumentInfo: name={info.file_name}")
    blocks = loader.load_blocks(EXCEL_FILE, info)
    first = next(iter(blocks))
    print(f"First block: {first.text[:200]!r}")
    print(f"Metadata: {first.metadata}")


if __name__ == "__main__":
    demo_text_loader()
    demo_markdown_loader()
    demo_csv_loader()
    demo_pdf_loader()
    demo_excel_loader()
