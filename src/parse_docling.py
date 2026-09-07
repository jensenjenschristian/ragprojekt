import json
import re
from pathlib import Path

SECTION_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")


def split_heading(text):
    """Split '6.4 Afregning af materialeforbrug' into ('6.4', 'Afregning...').

    Returns (None, text) for unnumbered headings like 'Særligt vedr. sikkerhed'.
    """
    m = SECTION_NUM.match(text.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, text.strip()

DROP_LABELS = {"page_footer", "page_header"}
HEADING_LABELS = {"section_header", "title"}

def _resolve(ref, doc):
    """Follow a JSON pointer like '#/texts/12' into the parsed document."""
    parts = ref.lstrip("#/").split("/")
    node = doc
    for p in parts:
        node = node[int(p)] if p.isdigit() else node[p]
    return node


def serialise_table(tbl):
    """Render a table's cells as one line per row, cells separated by ' | '."""
    cells = tbl.get("data", {}).get("table_cells", [])
    rows = {}
    for c in cells:
        r = c.get("start_row_offset_idx", 0)
        rows.setdefault(r, []).append(
            (c.get("start_col_offset_idx", 0), (c.get("text") or "").strip())
        )
    lines = []
    for r in sorted(rows):
        ordered = [txt for _, txt in sorted(rows[r]) if txt]
        if ordered:
            lines.append(" | ".join(ordered))
    return "\n".join(lines)


def load_elements(json_path):
    """Walk a Docling JSON in reading order, carrying section state."""
    doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
    source = Path(json_path).stem

    section = None
    section_path = None
    subsection = None

    out = []
    for child in doc.get("body", {}).get("children", []):
        ref = child.get("$ref", "")
        node = _resolve(ref, doc)
        page = (node.get("prov") or [{}])[0].get("page_no")

        if ref.startswith("#/tables/"):
            text = serialise_table(node)
            label = "table"
        elif ref.startswith("#/texts/"):
            label = node.get("label")
            text = (node.get("text") or "").strip()
            if label in DROP_LABELS:
                continue
            if label in HEADING_LABELS:
                num, title = split_heading(text)
                if num:
                    section_path, section, subsection = num, text, None
                else:
                    subsection = title
                continue
        else:
            continue    # pictures and anything else

        if not text:
            continue

        out.append({
            "text": text,
            "source": source,
            "page": page,
            "section": section,
            "section_path": section_path,
            "subsection": subsection,
            "element_type": label,
        })
    return out