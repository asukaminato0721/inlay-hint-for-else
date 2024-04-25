from typing import List
from lsprotocol.types import InlayHint, InlayHintKind, InlayHintParams, Position
from pygls.server import LanguageServer
from utils import extract_conditions, merge

server = LanguageServer("else inlay hint", "0.0.1")


@server.feature("textDocument/inlayHint")
def inlay_hint(ls: LanguageServer, params: InlayHintParams):
    hints: List[InlayHint] = []
    text = ls.workspace.get_text_document(params.text_document.uri)
    for line, offset, stmt in merge(extract_conditions(text.source)):
        hints.append(
            InlayHint(Position(line, offset + 1), "# " + stmt, kind=InlayHintKind.Parameter)
        )
    return hints


if __name__ == "__main__":
    print("server start")
    server.start_io()
    print("server end")
