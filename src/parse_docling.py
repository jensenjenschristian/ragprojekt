import json
import re
from pathlib import Path

SECTION_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
DELAFTALE_GROUP = re.compile(r"Tilbudsliste\s*-\s*(.+)$", re.IGNORECASE)
DROP_LABELS = {"page_footer", "page_header"}
HEADING_LABELS = {"section_header", "title"}

EXCLUDE_DOCS = {
    # Situationsplaner: CAD exports. Text is building IDs and street labels
    # (Fib 11, ANVAlfred Nobels Vej) meaningful only by position on the drawing.
    # 88 elements, 13% of the corpus, none of it answerable.
    "Bilag 6A - Situationsplan for AAU Aalborg Øst",
    "Bilag 6B - Situationsplan for AAU Aalborg city",
    "Bilag 6C - Situationsplan for AAU Esbjerg",
    "Bilag 6D - Situationsplan for AAU CPH",
}


def load_corpus(parsed_dir="data-parsed", exclude=True):
    """Load all documents, optionally applying curation exclusions."""
    out = []
    for f in sorted(Path(parsed_dir).glob("*.json")):
        if exclude and f.stem in EXCLUDE_DOCS:
            continue
        for el in load_elements(f):
            if exclude and _is_front_matter(el):
                continue
            out.append(el)
    return out


def _is_front_matter(el):
    """Front-matter tables: no section assigned yet, so they precede the first
    heading. Catches the ToC, whose dot-leader typography TableFormer
    misdetected as a 21x2 grid."""
    return el["element_type"] == "table" and el["section"] is None

def split_heading(text):
    """Split '6.4 Afregning af materialeforbrug' into ('6.4', 'Afregning...').

    Returns (None, text) for unnumbered headings like 'Særligt vedr. sikkerhed'.
    """
    m = SECTION_NUM.match(text.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, text.strip()

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

    st = {"section": None, "section_path": None,
          "subsection": None, "delaftale": None}
    out = []

    def walk(children):
        for child in children:
            ref = child.get("$ref", "")
            node = _resolve(ref, doc)

            if ref.startswith("#/groups/"):
                name = node.get("name") or ""
                m = DELAFTALE_GROUP.search(name)
                if m:
                    st["delaftale"] = m.group(1).strip()
                    st["section"] = name
                    st["section_path"] = None
                    st["subsection"] = None
                walk(node.get("children", []))
                continue

            page = (node.get("prov") or [{}])[0].get("page_no")

            if ref.startswith("#/tables/"):
                data = node.get("data", {})
                text = serialise_table(node)
                if data.get("num_rows") == 1 and data.get("num_cols") == 1:
                    st["section"] = text        # 1x1 table is a heading
                    st["subsection"] = None
                    continue
                label = "table"
            elif ref.startswith("#/texts/"):
                label = node.get("label")
                text = (node.get("text") or "").strip()
                if label in DROP_LABELS:
                    continue
                if label in HEADING_LABELS:
                    num, title = split_heading(text)
                    if num:
                        st["section_path"] = num
                        st["section"] = text
                        st["subsection"] = None
                    else:
                        st["subsection"] = title
                    continue
            else:
                continue

            if not text:
                continue

            out.append({
                "text": text,
                "source": source,
                "page": page,
                "section": st["section"],
                "section_path": st["section_path"],
                "subsection": st["subsection"],
                "delaftale": st["delaftale"],
                "element_type": label,
            })

    walk(doc.get("body", {}).get("children", []))
    return out

def filter_elements(elements, **criteria):
    """Filter by exact match on any metadata field.

    filter_elements(els, source="Bilag 3 - Kravspecifikation")
    filter_elements(els, delaftale="København", element_type="table")
    """
    out = elements
    for field, value in criteria.items():
        out = [e for e in out if e.get(field) == value]
    return out