from exam_review_skill.chunk import chunk_documents
from exam_review_skill.models import Document, DocumentBlock


def test_chunk_preserves_source_metadata():
    doc = Document(
        source_file="lecture.txt",
        doc_type="lecture_slide",
        blocks=[DocumentBlock(source_file="lecture.txt", page_or_slide="2", heading="标准溶液", content="重点：标准溶液用于滴定分析。")],
    )
    chunks = chunk_documents([doc])
    assert chunks
    ch = chunks[0]
    assert ch.source_file == "lecture.txt"
    assert ch.page_or_slide == "2"
    assert ch.heading == "标准溶液"
    assert "标准溶液" in ch.content
