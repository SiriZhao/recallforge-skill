from __future__ import annotations

import re

from .models import Chunk, Document


KEYWORDS = ["重点", "必考", "误差", "滴定", "标准溶液", "有效数字", "公式", "计算", "实验步骤", "陷阱", "答案"]


def _keywords(text: str) -> list[str]:
    found = [k for k in KEYWORDS if k in text]
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,6}", text):
        if token not in found and len(found) < 8:
            found.append(token)
    return found[:8]


def chunk_documents(docs: list[Document], max_chars: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    seq = 1
    for doc in docs:
        for block in doc.blocks:
            pieces = [block.content]
            if len(block.content) > max_chars:
                pieces = re.split(r"(?<=。)|(?<=；)|\n(?=第?\s*\d+\s*[题、.])", block.content)
            buf = ""
            for piece in pieces:
                piece = piece.strip()
                if not piece:
                    continue
                if len(buf) + len(piece) > max_chars and buf:
                    chunks.append(_make_chunk(seq, block, buf))
                    seq += 1
                    buf = piece
                else:
                    buf = (buf + "\n" + piece).strip()
            if buf:
                chunks.append(_make_chunk(seq, block, buf))
                seq += 1
    return chunks


def _make_chunk(seq: int, block, content: str) -> Chunk:
    kws = _keywords(content)
    possible = []
    if any(k in content for k in ["重点", "必考", "容易考", "往年", "计算题", "简答题"]):
        possible.append((block.heading or kws[0] if kws else "未命名考点"))
    return Chunk(
        chunk_id=f"CH{seq:04d}",
        source_file=block.source_file,
        page_or_slide=block.page_or_slide,
        question_number=block.question_number,
        doc_type=block.doc_type,
        chapter=block.chapter,
        heading=block.heading,
        content=content,
        keywords=kws,
        possible_exam_points=possible,
        confidence=block.confidence,
        source_refs=block.source_refs,
    )
