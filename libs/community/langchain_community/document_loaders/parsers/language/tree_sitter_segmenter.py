from abc import abstractmethod
from typing import TYPE_CHECKING, List

from langchain_community.document_loaders.parsers.language.code_segmenter import (
    CodeSegmenter,
)

if TYPE_CHECKING:
    from tree_sitter import Language, Node, Parser

TREE_SITTER_ERR_MESSAGE = (
    "Could not import tree_sitter/tree_sitter_language_pack Python packages."
    "Please install them with "
    "`pip install tree-sitter tree-sitter-language-pack`."
)


class TreeSitterSegmenter(CodeSegmenter):
    """Abstract class for `CodeSegmenter`s that use the tree-sitter library."""

    def __init__(self, code: str):
        super().__init__(code)
        self.source_lines = self.code.splitlines()

        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_language_pack  # noqa: F401
        except ImportError:
            raise ImportError(TREE_SITTER_ERR_MESSAGE)

    def is_valid(self) -> bool:
        from tree_sitter import Query, QueryCursor

        language = self.get_language()
        error_query = Query(language, "(ERROR) @error")

        parser = self.get_parser()
        tree = parser.parse(bytes(self.code, encoding="UTF-8"))

        cursor = QueryCursor(error_query)
        captures = cursor.captures(tree.root_node)
        return len(captures.get("error", [])) == 0

    def extract_functions_classes(self) -> List[str]:
        from tree_sitter import Query, QueryCursor

        language = self.get_language()
        query = Query(language, self.get_chunk_query())

        parser = self.get_parser()
        tree = parser.parse(bytes(self.code, encoding="UTF-8"))

        cursor = QueryCursor(query)
        query_captures: dict[str, list[Node]] = cursor.captures(tree.root_node)

        # Collect all nodes and sort by start line to process in order
        all_nodes = []
        for nodes in query_captures.values():
            all_nodes.extend(nodes)

        # Sort by start line, then by size (larger nodes first for same start line)
        all_nodes.sort(
            key=lambda n: (n.start_point[0], -(n.end_point[0] - n.start_point[0]))
        )

        processed_lines: set[int] = set()
        chunks: list[str] = []

        for node in all_nodes:
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = range(start_line, end_line + 1)

            if any(line in processed_lines for line in lines):
                continue

            processed_lines.update(lines)
            if node.text:
                chunk_text = node.text.decode("UTF-8")
                chunks.append(chunk_text)

        return chunks

    def simplify_code(self) -> str:
        from tree_sitter import Query, QueryCursor

        language = self.get_language()
        query = Query(language, self.get_chunk_query())

        parser = self.get_parser()
        tree = parser.parse(bytes(self.code, encoding="UTF-8"))

        cursor = QueryCursor(query)
        captures: dict[str, list] = cursor.captures(tree.root_node)

        # Collect all nodes and sort by start line to process in order
        all_nodes = []
        for nodes in captures.values():
            all_nodes.extend(nodes)

        # Sort by start line, then by size (larger nodes first for same start line)
        all_nodes.sort(
            key=lambda n: (n.start_point[0], -(n.end_point[0] - n.start_point[0]))
        )

        processed_lines: set[int] = set()
        simplified_lines = self.source_lines[:]

        for node in all_nodes:
            start_line = node.start_point[0]
            end_line = node.end_point[0]

            # Clamp end_line to the actual number of lines we have
            max_line = len(simplified_lines) - 1
            end_line = min(end_line, max_line)

            lines = list(range(start_line, end_line + 1))
            if any(line in processed_lines for line in lines):
                continue

            if start_line < len(simplified_lines):
                simplified_lines[start_line] = self.make_line_comment(
                    f"Code for: {self.source_lines[start_line]}"
                )
                for line_num in range(start_line + 1, end_line + 1):
                    if line_num < len(simplified_lines):
                        simplified_lines[line_num] = None  # type: ignore[call-overload]

            processed_lines.update(lines)

        return "\n".join(line for line in simplified_lines if line is not None)

    def get_parser(self) -> "Parser":
        from tree_sitter import Parser

        parser = Parser(self.get_language())
        return parser

    @abstractmethod
    def get_language(self) -> "Language":
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_chunk_query(self) -> str:
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def make_line_comment(self, text: str) -> str:
        raise NotImplementedError()  # pragma: no cover
