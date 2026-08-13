"""Real local OCR benchmark with self-authored ground truth.

Metrics: CER, WER where meaningful, elapsed time, pages/sec, cold start,
provider version, and install footprint. Host vision is intentionally not
measured here because it depends on the selected host/model.
"""

from __future__ import annotations

import json
import statistics
import platform
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks.ocr_fixtures import build_fixtures


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def _cer(reference: str, hypothesis: str) -> float:
    ref = _norm(reference)
    hyp = _norm(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    previous = list(range(len(hyp) + 1))
    for i, ref_ch in enumerate(ref, 1):
        current = [i]
        for j, hyp_ch in enumerate(hyp, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ref_ch != hyp_ch),
            ))
        previous = current
    return previous[-1] / len(ref)


def _wer(reference: str, hypothesis: str) -> float | None:
    ref_words = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", reference.lower())
    hyp_words = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", hypothesis.lower())
    if not ref_words:
        return None
    if len(ref_words) == 1 and not re.search(r"[A-Za-z]", reference):
        # Character-level metric is the meaningful one for pure Chinese text.
        return None
    previous = list(range(len(hyp_words) + 1))
    for i, ref_w in enumerate(ref_words, 1):
        current = [i]
        for j, hyp_w in enumerate(hyp_words, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ref_w != hyp_w),
            ))
        previous = current
    return previous[-1] / len(ref_words)


def _package_size(package_names: list[str]) -> int:
    site = Path(sys.prefix) / "Lib" / "site-packages"
    total = 0
    for name in package_names:
        candidates = [
            site / name,
            site / (name.replace("-", "_")),
            *site.glob(f"{name.replace('-', '_')}-*.dist-info"),
        ]
        for candidate in candidates:
            if candidate.is_dir():
                total += sum(p.stat().st_size for p in candidate.rglob("*") if p.is_file())
    return total


def _tesseract_path() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),):
        if candidate.exists():
            return str(candidate)
    return None


def _run_tesseract(fixture_path: Path, language: str) -> tuple[str, float]:
    import pytesseract

    tesseract_cmd = _tesseract_path()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    start = time.perf_counter()
    text = pytesseract.image_to_string(str(fixture_path), lang=language)
    return text, time.perf_counter() - start


def _run_rapidocr(engine, fixture_path: Path) -> tuple[str, float]:
    start = time.perf_counter()
    result, _elapse = engine(str(fixture_path))
    elapsed = time.perf_counter() - start
    if not result:
        return "", elapsed
    return "\n".join(item[1] for item in result), elapsed


def run() -> dict:
    providers = {}
    tesseract_path = _tesseract_path()
    if tesseract_path:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            version = str(pytesseract.get_tesseract_version()).split("\n")[0]
            providers["tesseract"] = {
                "status": "available", "version": version,
                "install_footprint_bytes": sum(
                    p.stat().st_size for p in Path(tesseract_path).parent.rglob("*") if p.is_file()
                ),
            }
        except Exception as exc:
            providers["tesseract"] = {"status": "unavailable", "error": str(exc)}
    else:
        providers["tesseract"] = {"status": "not_installed"}

    rapid_engine = None
    rapid_cold_start = None
    try:
        import rapidocr_onnxruntime
        from rapidocr_onnxruntime import RapidOCR
        from importlib.metadata import version as package_version
        cold_start = time.perf_counter()
        rapid_engine = RapidOCR()
        rapid_cold_start = time.perf_counter() - cold_start
        providers["rapidocr"] = {
            "status": "available",
            "version": package_version("rapidocr-onnxruntime"),
            "install_footprint_bytes": _package_size([
                "rapidocr_onnxruntime", "onnxruntime", "opencv_python",
                "numpy", "pyclipper", "shapely", "flatbuffers", "protobuf",
            ]),
        }
    except Exception as exc:
        providers["rapidocr"] = {"status": "unavailable", "error": str(exc)}

    with tempfile.TemporaryDirectory() as tmp:
        fixture_dir = Path(tmp) / "fixtures"
        fixture_dir.mkdir()
        fixtures = build_fixtures(fixture_dir)
        rows = []
        for fixture in fixtures:
            path = fixture_dir / f"{fixture.name}.png"
            entry = {
                "fixture": fixture.name,
                "kind": fixture.kind,
                "ground_truth": fixture.ground_truth,
                "engines": {},
            }
            if "tesseract" in providers and providers["tesseract"]["status"] == "available":
                try:
                    text, elapsed = _run_tesseract(path, fixture.language)
                    entry["engines"]["tesseract"] = {
                        "text": text.strip(),
                        "elapsed_seconds": round(elapsed, 4),
                        "cer": round(_cer(fixture.ground_truth, text), 4),
                        "wer": _wer(fixture.ground_truth, text),
                    }
                except Exception as exc:
                    entry["engines"]["tesseract"] = {"error": str(exc)}
            if "rapidocr" in providers and providers["rapidocr"]["status"] == "available":
                try:
                    text, elapsed = _run_rapidocr(rapid_engine, path)
                    entry["engines"]["rapidocr"] = {
                        "text": text.strip(),
                        "elapsed_seconds": round(elapsed, 4),
                        "cer": round(_cer(fixture.ground_truth, text), 4),
                        "wer": _wer(fixture.ground_truth, text),
                    }
                except Exception as exc:
                    entry["engines"]["rapidocr"] = {"error": str(exc)}
            rows.append(entry)

    summary = {}
    for engine_name in providers:
        entries = [
            row["engines"][engine_name]
            for row in rows
            if engine_name in row.get("engines", {})
            and "cer" in row["engines"][engine_name]
        ]
        if not entries:
            summary[engine_name] = {"status": "no_usable_results"}
            continue
        elapsed = sum(entry["elapsed_seconds"] for entry in entries)
        wer_values = [entry["wer"] for entry in entries if entry.get("wer") is not None]
        summary[engine_name] = {
            "fixtures_with_cer": len(entries),
            "mean_cer": round(statistics.mean(entry["cer"] for entry in entries), 4),
            "median_cer": round(statistics.median(entry["cer"] for entry in entries), 4),
            "mean_wer": round(statistics.mean(wer_values), 4) if wer_values else None,
            "total_elapsed_seconds": round(elapsed, 4),
            "pages_per_second": round(len(entries) / elapsed, 3) if elapsed else None,
            "failures": sum(1 for entry in entries if "error" in entry),
        }
        if engine_name == "rapidocr" and rapid_cold_start is not None:
            summary[engine_name]["cold_start_seconds"] = round(rapid_cold_start, 4)

    result = {
        "reference": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported",
            "gpu": "not used",
            "scope": "local CPU OCR only; host vision and formula interpretation excluded",
        },
        "providers": providers,
        "fixtures": rows,
        "summary": summary,
    }
    return result


if __name__ == "__main__":
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = json.dumps(run(), ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(payload)
