from __future__ import annotations

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple

import fitz  # PyMuPDF
import pymupdf4llm
from paddleocr import PaddleOCR, LayoutDetection
from tqdm import tqdm

TEXT_THRESHOLD = 50
OCR_DPI = 220
LAYOUT_MODEL_NAME = "PP-DocLayoutV3"


def to_jsonable(obj: Any) -> Any:
    """Convert PaddleOCR / PyMuPDF objects into plain JSON-serializable data."""
    if hasattr(obj, "json"):
        try:
            return to_jsonable(obj.json)
        except Exception:
            pass

    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]

    if isinstance(obj, Path):
        return str(obj)

    return obj


def extract_text_fields(obj: Any) -> List[str]:
    """
    Best-effort text collector for PaddleOCR JSON.
    It walks nested structures and collects string values from common text keys.
    """
    text_keys = {"text", "txt", "rec_text", "transcription", "content"}
    out: List[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in text_keys and isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    out.append(cleaned)
            else:
                out.extend(extract_text_fields(value))

    elif isinstance(obj, list):
        for item in obj:
            out.extend(extract_text_fields(item))

    return out


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def page_has_enough_native_text(page: fitz.Page, threshold: int = TEXT_THRESHOLD) -> bool:
    text = page.get_text("text").strip()
    return len(text) >= threshold


def render_page_to_png(page: fitz.Page, out_path: Path, dpi: int = OCR_DPI) -> None:
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    pix.save(str(out_path))


def extract_native_page_chunks(pdf_path: str) -> Dict[int, Dict[str, Any]]:
    """
    PyMuPDF4LLM page chunks are easier to work with than one giant markdown blob.
    Each page chunk includes metadata and the extracted text for that page.
    """
    chunks = pymupdf4llm.to_markdown(
        pdf_path,
        page_chunks=True,
        table_strategy="lines_strict",
        show_progress=True,
    )

    by_page: Dict[int, Dict[str, Any]] = {}
    for chunk in chunks:
        if isinstance(chunk, dict):
            metadata = chunk.get("metadata", {})
            page_number = metadata.get("page_number")
            if page_number is not None:
                by_page[int(page_number)] = to_jsonable(chunk)
    return by_page


def extract_scanned_page_with_paddleocr(
        page: fitz.Page,
        ocr_model: PaddleOCR,
        layout_model: LayoutDetection,
        tmpdir: Path,
) -> Dict[str, Any]:
    img_path = tmpdir / f"page_{page.number + 1}.png"
    render_page_to_png(page, img_path)

    layout_results = layout_model.predict(str(img_path), batch_size=1, layout_nms=True)
    ocr_results = ocr_model.predict(str(img_path))

    layout_json = [to_jsonable(res) for res in layout_results]
    ocr_json = [to_jsonable(res) for res in ocr_results]

    ocr_text = unique_preserve_order(extract_text_fields(ocr_json))

    return {
        "page": page.number + 1,
        "mode": "ocr",
        "layout": layout_json,
        "ocr": ocr_json,
        "ocr_text": "\n".join(ocr_text),
    }


def process_tender_pdf(pdf_path: str, max_workers: int = 4) -> Dict[str, Any]:
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_file))
    total_pages = len(doc)

    print("Step 1/4 — Extracting native text chunks…")
    native_chunks = extract_native_page_chunks(str(pdf_file))

    # PaddleOCR 3.x pipelines (initialised once, reused for all pages)
    print("Step 2/4 — Loading OCR / layout models…")
    ocr_model = PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    layout_model = LayoutDetection(model_name=LAYOUT_MODEL_NAME)

    output: Dict[str, Any] = {
        "pdf_path": str(pdf_file),
        "pages": [None] * total_pages,   # pre-sized so order is preserved
        "combined_text": "",
    }

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)

        # ── Classify pages & render scanned ones to PNG in parallel ──────────
        native_pages: List[Tuple[int, fitz.Page]] = []
        scanned_page_nos: List[int] = []
        img_paths: List[str] = []

        print("Step 3/4 — Classifying pages & rendering scanned pages…")
        def render_scanned(page: fitz.Page) -> Tuple[int, str]:
            img_path = tmpdir / f"page_{page.number + 1}.png"
            render_page_to_png(page, img_path)
            return page.number, str(img_path)

        # In process_tender_pdf, fix pages_list for PyMuPDF compatibility
        pages_list = [doc.load_page(i) for i in range(total_pages)]
        render_futures = {}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for page in pages_list:
                native_text = page.get_text("text").strip()
                native_chunk = native_chunks.get(page.number + 1)
                if len(native_text) >= TEXT_THRESHOLD and native_chunk is not None:
                    native_pages.append((page.number, page))
                else:
                    render_futures[pool.submit(render_scanned, page)] = page.number

            for fut in tqdm(as_completed(render_futures), total=len(render_futures),
                            desc="  Rendering scanned pages", unit="page"):
                page_no_0, img_path = fut.result()
                scanned_page_nos.append(page_no_0)
                img_paths.append(img_path)

        # ── Batch OCR + layout for all scanned pages ──────────────────────────
        print("Step 4/4 — Running OCR & layout detection (batch)…")
        if img_paths:
            # Sort by page order so tqdm progress is meaningful
            paired = sorted(zip(scanned_page_nos, img_paths), key=lambda x: x[0])
            if paired:
                scanned_page_nos, img_paths = zip(*paired)
                scanned_page_nos = list(scanned_page_nos)
                img_paths = list(img_paths)
            else:
                scanned_page_nos = []
                img_paths = []

            ocr_results_all   = ocr_model.predict(list(img_paths))
            layout_results_all = layout_model.predict(list(img_paths), batch_size=len(img_paths), layout_nms=True)

            for idx, page_no_0 in enumerate(tqdm(scanned_page_nos, desc="  Assembling OCR pages", unit="page")):
                ocr_json    = [to_jsonable(ocr_results_all[idx])]
                layout_json = [to_jsonable(layout_results_all[idx])]
                ocr_text    = unique_preserve_order(extract_text_fields(ocr_json))
                output["pages"][page_no_0] = {
                    "page":     page_no_0 + 1,
                    "mode":     "ocr",
                    "layout":   layout_json,
                    "ocr":      ocr_json,
                    "ocr_text": "\n".join(ocr_text),
                }
        else:
            scanned_page_nos = []
            img_paths = []

        # ── Native text pages (fast, parallel) ───────────────────────────────
        def build_native(args: Tuple[int, fitz.Page]) -> Tuple[int, Dict[str, Any]]:
            page_no_0, page = args
            page_no   = page_no_0 + 1
            native_text  = page.get_text("text").strip()
            native_chunk = native_chunks.get(page_no)
            return page_no_0, {
                "page":  page_no,
                "mode":  "native_text",
                "text":  native_text,
                "chunk": native_chunk,
            }

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for page_no_0, data in tqdm(
                pool.map(build_native, native_pages),
                total=len(native_pages),
                desc="  Assembling native pages",
                unit="page",
            ):
                output["pages"][page_no_0] = data

    # ── Combine text in page order ────────────────────────────────────────────
    combined_parts: List[str] = []
    for page_data in output["pages"]:
        if page_data is None:
            continue
        text = page_data.get("text") or page_data.get("ocr_text") or ""
        if text.strip():
            combined_parts.append(text.strip())

    output["combined_text"] = "\n\n".join(combined_parts)
    return output


def main():
    pdf_path = "Smart_City_Tender_Document.pdf"
    out_path = Path("tender_extracted.json")
    print("[1/4] Opening {}...".format(pdf_path))
    result = process_tender_pdf(pdf_path)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
