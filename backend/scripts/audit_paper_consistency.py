# -*- coding: utf-8 -*-
import sys
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('Bai_Bao_Khoa_Hoc_Acamind_Hoan_Chinh.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

patterns = [
    '35.2', '21.9', '33.8', '20.5',
    '250.0', '212.6', '247.2',
    '2.49', '1.92', '1.38', '1.70', '2.24',
    '0.675', '0.655', '0.656', '0.632', '0.6875', '0.668', '0.688',
    '499', '500', '9.688', '9,688', '70.794', '70,794', '12.411', '12,411',
    'N = 8', 'N=8', 'N = 50', 'N=50'
]

print("=== CHECKING MARKDOWN TEXT FOR POTENTIAL INCONSISTENCIES ===")
for pat in patterns:
    matches = [m.start() for m in re.finditer(re.escape(pat), md_text)]
    print(f'Pattern "{pat}": {len(matches)} occurrences')
    for idx in matches:
        snippet = md_text[max(0, idx-50):min(len(md_text), idx+70)].replace('\n', ' ')
        print(f'   -> ...{snippet}...')
