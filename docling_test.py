import psutil, time
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

#testede den mindste først
#PDF = "data/Bilag 9 - Tro- og loveerklæring vedr. forordning.pdf"
PDF = "data/Bilag 5 - Vejledning til eksterne samarbejdspartnere - version august 2024.pdf"

proc = psutil.Process()
print(f"RSS before: {proc.memory_info().rss / 1e6:.0f} MB")

opts = PdfPipelineOptions()
opts.do_table_structure = False    # rung 2 of the mitigation ladder, up front
opts.do_ocr = False                # text layer exists; OCR would waste RAM

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)

t0 = time.time()
result = converter.convert(PDF)
#result = converter.convert(PDF, page_range=(10, 10))

elapsed = time.time() - t0

md = result.document.export_to_markdown()
Path("notes/docling-sample.md").write_text(md, encoding="utf-8")

print(f"RSS after:  {proc.memory_info().rss / 1e6:.0f} MB")
print(f"Peak:       {proc.memory_info().peak_wset / 1e6:.0f} MB")
print(f"Time:       {elapsed:.1f}s")
print(f"Chars:      {len(md)}")