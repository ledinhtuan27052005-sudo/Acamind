import sys
import os
import fitz

f = r'C:\Users\Admin\Desktop\Acamind\data\raw_pdfs\bfc5899b-cc61-453a-a6a6-163234b0ce85_Tai_Lieu_Scan_Thu_Nghiem_CBT_Tam_Ly_Hoc.pdf'
doc = fitz.open(f)
p2 = doc[1]

words = p2.get_text('words')
# Find words that match 68.9%
matches = [w for w in words if '68.9%' in w[4]]
print(f"Found {len(matches)} matches for 68.9% in words")

for m in matches:
    # Get all words on the same line
    same_line = [w for w in words if w[5] == m[5] and w[6] == m[6]]
    x0 = min(w[0] for w in same_line)
    y0 = min(w[1] for w in same_line)
    x1 = max(w[2] for w in same_line)
    y1 = max(w[3] for w in same_line)
    r = fitz.Rect(x0, y0, x1, y1)
    print("Highlighting Line Rect:", r)
    print("  Line text:", " ".join(w[4] for w in same_line))
    annot = p2.add_highlight_annot(r)
    annot.set_colors(stroke=(1.0, 0.88, 0.20))
    annot.update()

out_path = "C:/Users/Admin/.gemini/antigravity/brain/13f2f52f-1f4c-415f-8985-722bfe78a66f/verified_cbt_line_highlight.png"
pix = p2.get_pixmap(dpi=150)
pix.save(out_path)
print("Saved rendered page to:", out_path)
