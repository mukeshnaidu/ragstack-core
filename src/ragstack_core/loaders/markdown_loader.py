import re
from collections.abc import Iterator
from pathlib import Path

from ragstack_core.loaders.base_loader import BaseLoader
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_info import DocumentInfo

_HEADING_RE = re.compile(r"^(#{1,6} .+)$", re.MULTILINE)
_FENCE_RE = re.compile(r"^(`{3,}|~{3,}).*?\n.*?\n\1$", re.MULTILINE | re.DOTALL)


class MarkdownLoader(BaseLoader):
    def load_info(self, file_path: str | Path) -> DocumentInfo:
        return DocumentInfo.from_path(file_path)

    def load_blocks(
        self,
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        content = Path(file_path).read_text(encoding="utf-8")
        sections = self._split_sections(content)
        section_index = 0

        for heading, level, body in sections:
            if heading:
                text = f"{'#' * level} {heading}\n{body}".strip()
            else:
                text = body.strip()

            if not text:
                continue

            yield self._create_block(
                document_info=document_info,
                block_index=section_index,
                text=text,
                heading=heading,
                heading_level=level,
                section_index=section_index,
            )
            section_index += 1

    def _split_sections(self, content: str) -> list[tuple[str, int, str]]:
        # Temporarily hide fenced code blocks so we don't split on comments inside them
        fences = []

        def _repl(match):
            fences.append(match.group(0))
            return f"\n__RAGSTACK_FENCE_{len(fences) - 1}__\n"

        safe_content = _FENCE_RE.sub(_repl, content)

        parts = _HEADING_RE.split(safe_content)
        sections: list[tuple[str, int, str]] = []

        def _restore(text: str) -> str:
            for i, fence in enumerate(fences):
                text = text.replace(f"__RAGSTACK_FENCE_{i}__", fence)
            return text

        if parts[0].strip():
            sections.append(("", 0, _restore(parts[0])))

        for i in range(1, len(parts), 2):
            heading_line = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            match = re.match(r"^(#{1,6})\s+(.+)$", heading_line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                sections.append((heading_text, level, _restore(body)))

        return sections

    def _create_block(
        self,
        document_info: DocumentInfo,
        block_index: int,
        text: str,
        heading: str,
        heading_level: int,
        section_index: int,
    ) -> DocumentBlock:
        return DocumentBlock(
            document_id=document_info.document_id,
            block_index=block_index,
            text=text,
            metadata={
                "file_name": document_info.file_name,
                "file_type": document_info.file_type,
                "source_path": document_info.source_path,
                "block_type": "section",
                "heading": heading,
                "heading_level": heading_level,
                "section_index": section_index,
            },
        )
