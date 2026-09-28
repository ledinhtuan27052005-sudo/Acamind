import docx
from docx.shared import Pt

def add_refs():
    doc = docx.Document('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')
    target_idx = None
    for i, p in enumerate(doc.paragraphs):
        if 'Thông tin tác giả' in p.text:
            target_idx = i
            break

    if target_idx:
        new_refs = [
            '[19] M. D. Skarlinski et al., "Paperqa2: Superhuman scientific literature question answering and summarization," arXiv preprint arXiv:2409.13740, 2024.',
            '[20] J. Jin et al., "Flashrag: A modular toolkit for efficient retrieval-augmented generation research," arXiv preprint arXiv:2405.13576, 2024.',
            '[21] D. Edge et al., "From local to global: A graph rag approach to query-focused summarization," arXiv preprint arXiv:2408.08921, 2024.'
        ]
        target_p = doc.paragraphs[target_idx]
        for ref_text in new_refs:
            p = target_p.insert_paragraph_before(ref_text)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
        doc.save('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')
        print('Added references [19], [20], [21] to docx')

if __name__ == '__main__':
    add_refs()
