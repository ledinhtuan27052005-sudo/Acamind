"""Targeted retrieval suggestions; relevance is not verified field extraction."""
from app.services.study_profile import FIELDS
from app.services.ranking_explanation import explain_ranking

QUERIES = {
    'objective': 'research question aim purpose objective',
    'method': 'study design methods procedures analysis',
    'sample': 'participants recruitment sample size population eligibility',
    'data': 'dataset data collection source corpus',
    'measure': 'measurement instrument scale questionnaire metric',
    'finding': 'study results findings effect estimates',
    'limitation': 'limitations bias uncertainty generalizability',
    'timepoint': 'assessment timing baseline follow-up duration',
    'comparator': 'intervention treatment control comparison group',
    'direction': 'score interpretation higher lower reverse coding',
}


def search_gap(document_id, criterion, focus, db):
    from app.services.retriever import retrieve
    if criterion not in FIELDS:
        raise ValueError('Unknown criterion')
    query = f'{FIELDS[criterion][0]}: {QUERIES[criterion]}. {focus.strip()}'
    hits = retrieve(query, [str(document_id)], db, top_k=5, rerank_top_n=30)
    # Reload original chunks in the route; never expose generated/enriched text as a quote.
    ids = []
    explanations = {}
    for position, hit in enumerate(hits, 1):
        if str(hit.get('document_id')) == str(document_id) and hit.get('id'):
            value = str(hit['id'])
            if value not in ids:
                ids.append(value)
                explanations[value] = explain_ranking(hit, position)
    return query, ids[:5], explanations
