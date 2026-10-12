import sys
import os
import fitz

sys.path.insert(0, os.path.abspath('backend'))
from app.services.pdf_highlighter import generate_highlighted_pdf_stream

out_dir = "C:/Users/Admin/.gemini/antigravity/brain/13f2f52f-1f4c-415f-8985-722bfe78a66f"

# 1. Render Paper 2609.13304v1.pdf Page 1
p1_stream = generate_highlighted_pdf_stream(
    'backend/data/raw_pdfs_500/2609.13304v1.pdf',
    1,
    "Psychology is the scientific study of human behavior and cognitive processes, developed historically as an approach to understand how the mind processes information"
)
doc1 = fitz.open(stream=p1_stream, filetype="pdf")
pix1 = doc1[0].get_pixmap(dpi=150)
pix1.save(os.path.join(out_dir, "test_render_2609_highlight.png"))
doc1.close()

# 2. Render Tai_Lieu_Scan_Thu_Nghiem_CBT_Tam_Ly_Hoc.pdf Page 2
p2_stream = generate_highlighted_pdf_stream(
    'data/raw_pdfs/bfc5899b-cc61-453a-a6a6-163234b0ce85_Tai_Lieu_Scan_Thu_Nghiem_CBT_Tam_Ly_Hoc.pdf',
    2,
    "Nhóm phối hợp CBT và SSRI đạt mức độ suy giảm triệu chứng trầm cảm vượt trội 68.9% so với hai nhóm đơn trị liệu"
)
doc2 = fitz.open(stream=p2_stream, filetype="pdf")
pix2 = doc2[1].get_pixmap(dpi=150)
pix2.save(os.path.join(out_dir, "test_render_cbt_p2_highlight.png"))
doc2.close()

print("Rendered both highlighted test pages to artifacts directory.")
