def chunk_fixed(elements, tok, size=250, overlap=50):
    """Week 1 baseline, in tokens rather than characters.

    Cuts every `size` tokens within a page, ignoring section, paragraph and
    sentence boundaries. Chunking per page (as Week 1 did) preserves page
    provenance; only the section metadata is unavailable.
    """
    chunks = []
    for source in sorted({e["source"] for e in elements}):
        els = [e for e in elements if e["source"] == source]
        pages = sorted({e["page"] for e in els if e["page"] is not None})
        for page in pages:
            page_els = [e for e in els if e["page"] == page]
            text = "\n".join(e["text"] for e in page_els)
            ids = tok.encode(text, add_special_tokens=False)
            step = size - overlap
            for i in range(0, len(ids), step):
                window = ids[i:i + size]
                if not window:
                    continue
                chunks.append({
                    "text": tok.decode(window),
                    "source": source,
                    "page": page,
                    "pages": [page],
                    "section": None,
                    "section_path": None,
                    "subsection": None,
                    "delaftale": None,
                    "element_type": "fixed",
                    "strategy": "fixed",
                })
    return chunks

def chunk_recursive(elements, tok, size=350, overlap=50):
    """Recursive split: keep whole elements together, pack up to `size` tokens.

    Respects element boundaries (paragraphs, list items, table rows) but not
    section boundaries — a chunk may span the end of 6.4 and the start of 6.5.
    """
    chunks = []
    for source in sorted({e["source"] for e in elements}):
        els = [e for e in elements if e["source"] == source]
        buf, buf_tokens = [], 0
        for e in els:
            n = len(tok.encode(e["text"], add_special_tokens=False))
            if buf and buf_tokens + n > size:
                chunks.append(_emit(buf, source, "recursive"))
                keep, kept = [], 0
                for prev in reversed(buf):
                    pn = len(tok.encode(prev["text"], add_special_tokens=False))
                    if kept + pn > overlap:
                        break
                    keep.insert(0, prev)
                    kept += pn
                buf, buf_tokens = keep, kept
            buf.append(e)
            buf_tokens += n
        if buf:
            chunks.append(_emit(buf, source, "recursive"))
    return chunks


def chunk_structural(elements, tok, size=400):
    """Group by section, splitting only when a section exceeds `size`.

    Boundaries fall where the document says they fall. Only possible because
    step 4 put section state on every element.
    """
    chunks = []
    key = lambda e: (e["source"], e["section"], e["delaftale"])
    current, buf, buf_tokens = None, [], 0
    for e in elements:
        k = key(e)
        n = len(tok.encode(e["text"], add_special_tokens=False))
        if k != current or (buf and buf_tokens + n > size):
            if buf:
                chunks.append(_emit(buf, buf[0]["source"], "structural"))
            buf, buf_tokens = [], 0
            current = k
        buf.append(e)
        buf_tokens += n
    if buf:
        chunks.append(_emit(buf, buf[0]["source"], "structural"))
    return chunks


def _emit(buf, source, strategy):
    first = buf[0]
    return {
        "text": "\n".join(e["text"] for e in buf),
        "source": source,
        "page": first["page"],
        "pages": sorted({e["page"] for e in buf if e["page"]}),
        "section": first["section"],
        "section_path": first["section_path"],
        "subsection": first["subsection"],
        "delaftale": first["delaftale"],
        "element_type": "group",
        "strategy": strategy,
    }