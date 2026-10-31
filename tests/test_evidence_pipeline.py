import sys
from pathlib import Path
import unittest
import threading
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import evidence_policy as policy
from app.services import reranker


class EvidencePolicyTests(unittest.TestCase):
    def test_comparison_uses_separate_verifier_model(self):
        from app.core.config import settings
        with patch.object(settings, "EVIDENCE_LOCAL_MODEL", "qwen2.5:3b-instruct"), \
             patch.object(settings, "EVIDENCE_COMPARISON_MODEL", "qwen3:4b-instruct"):
            self.assertEqual(policy.selected_evidence_model(["A"]), "qwen2.5:3b-instruct")
            self.assertEqual(policy.selected_evidence_model(["A", "B"]), "qwen3:4b-instruct")

    def test_missing_evidence_wording_does_not_claim_full_document_absence(self):
        answer = policy.qualify_missing_evidence(
            "Tài liệu không đề cập đến giải pháp trị liệu cụ thể. "
            "Không có thông tin về hạn chế trong tài liệu."
        )
        self.assertIn("Các đoạn được truy xuất chưa cho thấy giải pháp", answer)
        self.assertIn("chưa tìm thấy thông tin trong các đoạn được truy xuất về hạn chế", answer)

    def test_partial_comparison_renders_only_validated_quotes(self):
        matrix = {"cells": [
            {"target": "Study A", "facet": "finding", "status": "supported",
             "evidence": [{"quote": "A improved by 12 points", "filename": "a.pdf", "page": 3}]},
            {"target": "Study B", "facet": "finding", "status": "missing", "evidence": []},
        ]}
        answer = policy.render_verified_matrix(matrix)
        self.assertIn("A improved by 12 points” [a.pdf - Trang 3]", answer)
        self.assertIn("Chưa tìm thấy trong các đoạn được truy xuất", answer)
        self.assertNotIn("b.pdf - Trang", answer)

    def setUp(self):
        # Retrieval orchestration tests must not download/load a real embedding model.
        warmup = patch("app.services.retriever.embed_queries_batch_cached", return_value=[])
        warmup.start()
        self.addCleanup(warmup.stop)
        policy._CACHE.clear()
        reranker._PAIR_SCORE_CACHE.clear()
        self.chunks = [dict(id='1', document_id='a', doc_title='Study Alpha', doc_filename='alpha.pdf',
                            sub_query_target='Alpha', page_number=3,
                            content='The trial enrolled 120 participants at baseline.')]
        self.packet = policy.evidence_packet(['Alpha', 'Beta'], self.chunks)
        self.cell = dict(target='Alpha', facet='sample', status='supported', identity_matches=True,
                         source='0', quote='The trial enrolled 120 participants at baseline.')

    def test_missing_study_is_partial_not_complete(self):
        result = policy.validate_matrix({'cells': [self.cell]}, ['Alpha', 'Beta'], ['sample'], self.packet)
        self.assertEqual(result['action'], 'partial')
        self.assertEqual(result['supported_cells'], 1)

    def test_invented_quote_is_rejected(self):
        self.cell['quote'] = 'The trial enrolled 500 participants at baseline.'
        self.assertEqual(policy.validate_matrix({'cells': [self.cell]}, ['Alpha'], ['sample'], self.packet)['action'], 'refuse')

    def test_cross_study_source_is_rejected(self):
        self.cell['target'] = 'Beta'
        self.assertEqual(policy.validate_matrix({'cells': [self.cell]}, ['Beta'], ['sample'], self.packet)['action'], 'refuse')

    def test_uncertain_identity_is_not_support(self):
        self.cell['identity_matches'] = False
        self.assertEqual(policy.validate_matrix({'cells': [self.cell]}, ['Alpha'], ['sample'], self.packet)['action'], 'refuse')

    def test_keyword_only_cannot_create_evidence(self):
        self.assertEqual(policy.validate_matrix({'cells': []}, ['Alpha'], ['finding'], self.packet)['action'], 'refuse')

    def test_one_document_cannot_impersonate_two_studies(self):
        packet = self.packet + [{**self.packet[0], 'source': '1', 'target': 'Beta'}]
        result = policy.validate_matrix({'cells': [self.cell, {**self.cell, 'target': 'Beta', 'source': '1'}]},
                                        ['Alpha', 'Beta'], ['sample'], packet)
        self.assertEqual(result['supported_cells'], 1)

    def test_adaptive_budget_keeps_comparison_context(self):
        from app.services.retriever import adaptive_context_budget
        chunks = [{'rerank_score_available': True, 'rerank_score': 0.95},
                  {'rerank_score_available': True, 'rerank_score': 0.3}]
        self.assertEqual(adaptive_context_budget('How large was the sample?', chunks, 12), 6)
        self.assertEqual(adaptive_context_budget('Compare methods and results', chunks, 12), 12)
        self.assertEqual(adaptive_context_budget('How large was the sample?', [], 12), 12)

    def test_parent_page_not_used_as_source(self):
        self.chunks[0]['parent_context'] = 'Another page enrolled 999 participants.'
        self.assertNotIn('999', policy.evidence_packet(['Alpha'], self.chunks)[0]['text'])

    def test_unavailable_is_not_missing_evidence(self):
        with patch.object(policy, '_local_complete', side_effect=TimeoutError):
            result = policy.assess_evidence('sample', ['Alpha'], self.chunks)
        self.assertEqual(result['action'], 'unavailable')

    def test_cache_invalidates_on_content_change_and_returns_copy(self):
        with patch.object(policy, '_local_complete', return_value={'cells': [self.cell]}) as call:
            first = policy.assess_evidence('sample', ['Alpha'], self.chunks)
            first['cells'].clear()
            second = policy.assess_evidence('sample', ['Alpha'], self.chunks)
            self.assertEqual(len(second['cells']), 1)
            self.assertEqual(call.call_count, 1)
            self.chunks[0]['content'] += ' Updated.'
            policy.assess_evidence('sample', ['Alpha'], self.chunks)
            self.assertEqual(call.call_count, 2)

    def test_remote_verifier_is_rejected_before_network(self):
        from app.core.config import settings
        with patch.object(settings, 'OLLAMA_BASE_URL', 'https://example.com'), patch.object(policy.httpx, 'Client') as client:
            with self.assertRaises(ValueError):
                policy._local_complete({})
            client.assert_not_called()

    def test_batch_rerank_preserves_groups(self):
        scorer = MagicMock()
        scorer.score_pairs.return_value = [0.1, 0.9, 0.8]
        with patch.object(reranker, 'get_reranker', return_value=scorer), patch.object(reranker, '_env_use_llm_rerank', return_value=False):
            groups = reranker.rerank_groups([('A', [{'id': 'a1', 'content': 'one'}, {'id': 'a2', 'content': 'two'}]), ('B', [{'id': 'b', 'content': 'three'}])], 1)
        self.assertEqual([[c['id'] for c in group] for group in groups], [['a2'], ['b']])
        self.assertEqual(scorer.score_pairs.call_count, 1)

    def test_batch_cache_tracks_content_without_leaking_metadata(self):
        scorer = MagicMock()
        scorer.score_pairs.return_value = [0.8]
        with patch.object(reranker, 'get_reranker', return_value=scorer), patch.object(reranker, '_env_use_llm_rerank', return_value=False):
            reranker.rerank_groups([('A', [{'id': 'a1', 'content': 'text'}])], 1)
            second = reranker.rerank_groups([('A', [{'id': 'a2', 'content': 'text'}])], 1)
            self.assertEqual(scorer.score_pairs.call_count, 1)
            self.assertEqual(second[0][0]['id'], 'a2')
            reranker.rerank_groups([('A', [{'id': 'a2', 'content': 'changed text'}])], 1)
            self.assertEqual(scorer.score_pairs.call_count, 2)

    def test_batch_failure_has_no_fake_negative_scores(self):
        with patch.object(reranker, 'get_reranker', side_effect=RuntimeError):
            groups = reranker.rerank_groups([('A', [{'id': 'a'}])], 1)
        self.assertFalse(groups[0][0]['rerank_score_available'])

    def test_verifier_rejects_malformed_json_shape(self):
        with self.assertRaises(ValueError):
            policy.validate_matrix([], ['Alpha'], ['sample'], self.packet)

    def test_verifier_output_budget_scales_with_matrix_size(self):
        small = policy.verification_output_budget(['Alpha'], ['answer'])
        comparison = policy.verification_output_budget(
            ['Alpha', 'Beta'], ['sample', 'method', 'finding'])
        largest = policy.verification_output_budget(
            [f'Study {i}' for i in range(10)], ['sample', 'method', 'measure', 'finding'])
        self.assertEqual(small, 512)
        self.assertGreater(comparison, small)
        self.assertLessEqual(comparison, 3000)
        self.assertEqual(largest, 3000)

    def test_verifier_uses_budget_without_trimming_evidence(self):
        from app.core.config import settings
        class Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"message": {"content": '{"cells": []}'}}

        client = MagicMock()
        client.post.return_value = Response()
        payload = {"question": "sample", "targets": ["Alpha"], "facets": ["sample"],
                   "passages": [{"source": "0", "text": "Original passage remains intact."}]}
        with patch.object(policy, '_is_ollama_reachable', return_value=True), \
             patch.object(settings, 'EVIDENCE_LOCAL_MODEL', 'qwen3:4b'), \
             patch.object(policy.httpx, 'Client') as client_factory:
            client_factory.return_value.__enter__.return_value = client
            policy._local_complete(payload)
        sent = client.post.call_args.kwargs["json"]
        self.assertEqual(sent["options"]["num_predict"], 512)
        self.assertIs(sent["think"], False)
        self.assertIn("Original passage remains intact.", sent["messages"][1]["content"])

    def test_parallel_comparison_preserves_both_targets(self):
        from app.services import retriever
        barrier = threading.Barrier(2)
        def candidates(target, *args):
            barrier.wait(timeout=3)
            return [dict(id=target, document_id=target, content='Distinct evidence for ' + target,
                         page_number=1, sub_query_target=target, rrf_score=0.02)]
        with patch.object(retriever, '_retrieve_study_candidates', side_effect=candidates), \
             patch.object(retriever, '_enrich_parent_context', side_effect=lambda chunks, db: chunks), \
             patch.object(reranker, 'rerank_groups', side_effect=lambda groups, top_n: [cs for _, cs in groups]):
            result = retriever.retrieve('Compare "Study Alpha" and "Study Beta" on sample', None, MagicMock())
        self.assertEqual({c['sub_query_target'] for c in result}, {'Study Alpha', 'Study Beta'})
        self.assertIn('stage_timings_ms', result[0]['_telemetry'])

    def test_failed_target_does_not_discard_other_study(self):
        from app.services import retriever
        def candidates(target, *args):
            if target == 'Beta':
                raise RuntimeError('simulated DB failure')
            return [dict(id='a', document_id='a', content='Alpha evidence', page_number=1, sub_query_target=target)]
        with patch.object(retriever, '_retrieve_study_candidates', side_effect=candidates), \
             patch.object(retriever, '_enrich_parent_context', side_effect=lambda chunks, db: chunks), \
             patch.object(reranker, 'rerank_groups', side_effect=lambda groups, top_n: [cs for _, cs in groups]):
            result = retriever.retrieve('Compare "Alpha" and "Beta" on sample', None, MagicMock())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['sub_query_target'], 'Alpha')

    def test_study_lookup_keeps_explicit_document_scope(self):
        from app.services import retriever
        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        with patch.object(retriever, 'SessionLocal') as factory, \
             patch.object(retriever, '_retrieve_single_pass', return_value=[]) as search:
            factory.return_value.__enter__.return_value = session
            retriever._retrieve_study_candidates('Alpha', 'sample', ['allowed-id'], 20)
        self.assertEqual(search.call_args.args[1], ['allowed-id'])
        self.assertIs(search.call_args.args[2], session)
        self.assertFalse(session.execute.call_args.args[1]['all_docs'])

    def test_repair_is_bounded_and_preserves_existing_support(self):
        from app.services import retriever
        matrix = policy.validate_matrix({'cells': [self.cell]}, ['Alpha', 'Beta'], ['sample'], self.packet)
        with patch.object(policy, 'assess_evidence', side_effect=[matrix, {'action': 'unavailable', 'verification_ms': 1}]), \
             patch.object(retriever, 'retrieve', return_value=[dict(id='new', document_id='b', page_number=1, content='Other evidence')]) as search:
            result, chunks = policy.assess_and_repair('sample', ['Alpha', 'Beta'], self.chunks, ['a', 'b'], MagicMock())
        self.assertEqual(search.call_count, 1)
        self.assertEqual(result['action'], 'partial')
        self.assertEqual(chunks, self.chunks)

    def test_natural_vietnamese_comparison_decomposition(self):
        from app.services.retriever import classify_and_decompose_query
        route = classify_and_decompose_query(
            "So sánh rối loạn tăng động giảm chú ý và rối loạn phổ tự kỷ ở trẻ em về đặc điểm lâm sàng và hướng can thiệp."
        )
        self.assertEqual(route["route"], "cross_article_comparison")
        self.assertEqual(route["num_targets"], 2)
        self.assertEqual(route["sub_queries"], ["rối loạn tăng động giảm chú ý", "rối loạn phổ tự kỷ ở trẻ em"])
        self.assertIn("đặc điểm lâm sàng", route.get("comparison_focus", ""))

    def test_cjk_leakage_cleaned_from_stream(self):
        from app.api.v1.chat import _clean_cjk_leakage
        raw = (
            "Ví dụ, bản đồ 肥胖症的前景 (见 https://www.gov.uk/test) 提供了肥胖症复杂系统 [PMC8114409.pdf - Trang 1]. "
            "因此，从广义上讲，心理学是研究人类心理过程和行为的科学。\n"
            "Câu tiếng Việt chuẩn xác [2610.06615v1.pdf - Trang 1]."
        )
        cleaned = _clean_cjk_leakage(raw)
        self.assertNotRegex(cleaned, r"[\u4e00-\u9fff]")
        self.assertIn("Câu tiếng Việt chuẩn xác [2610.06615v1.pdf - Trang 1].", cleaned)


    def test_speculative_cascade_rerank_fast_commit_and_boundary(self):
        from app.services import reranker
        reranker._rerank_cache.clear()
        clear_winner = [
            {"id": "c1", "content": "CBT cognitive behavioral therapy for depression treatment outcomes", "doc_title": "CBT Depression Trial", "rrf_score": 0.032, "vector_score": 0.92, "entity_anchor_hit": 1.0},
            {"id": "c2", "content": "Unrelated nutrition sleep hygiene study", "doc_title": "Sleep Study", "rrf_score": 0.011, "vector_score": 0.41, "entity_anchor_hit": 0.0},
        ]
        with patch.dict("os.environ", {"RERANK_EXPERIMENTAL_FAST_COMMIT": "1"}), \
             patch.object(reranker, "get_reranker") as get_model:
            ranked = reranker.rerank("CBT cognitive behavioral therapy depression", clear_winner, top_n=2)
            get_model.assert_not_called()
            self.assertEqual(ranked[0]["id"], "c1")
            self.assertTrue(ranked[0].get("cascade_fast_commit"))

    def test_single_pass_batch_query_embedding(self):
        import numpy as np
        from app.services import embedder
        embedder._query_embed_cache.clear()
        fake_model = MagicMock()
        fake_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        with patch.object(embedder, "_get_local_model", return_value=fake_model):
            vecs = embedder.embed_queries_batch_cached(["truy vấn A", "truy vấn B", "truy vấn A"])
        self.assertEqual(fake_model.encode.call_count, 1)
        self.assertEqual(len(vecs), 3)
        self.assertEqual(vecs[0], [0.1, 0.2])
        self.assertEqual(vecs[1], [0.3, 0.4])

    def test_deep_vs_brief_mode_instructions_pico_and_evidence_matrix(self):
        from app.api.v1.chat import _normalize_mode_instruction
        deep_vi = _normalize_mode_instruction("[He thong: MODE=DEEP] Tâm lý học nghiên cứu những gì?", "vi")
        brief_vi = _normalize_mode_instruction("[He thong: MODE=BRIEF] Tâm lý học nghiên cứu những gì?", "vi")
        self.assertIn("PICO", deep_vi)
        self.assertIn("Evidence Synthesis Matrix", deep_vi)
        self.assertIn("Dong thuan & Khac biet", deep_vi)
        self.assertIn("2-4 cau", brief_vi)
        self.assertNotIn("PRISMA", brief_vi)

    def test_build_psychology_prompt_includes_authors_and_deep_rules(self):
        from app.services.generator import build_psychology_prompt
        msgs = build_psychology_prompt(
            "Tâm lý học là gì?",
            [{"doc_filename": "PsyArXiv_4qsut.pdf", "doc_title": "Comparing Watson's Behaviorism", "doc_authors": "Luiz Henrique Santana", "page_number": 1, "content": "Psychology studies behavior and mental processes."}],
            lang="vi",
        )
        self.assertIn("Evidence Synthesis Matrix", msgs[0]["content"])
        self.assertIn("PICO", msgs[0]["content"])
        self.assertIn("Authors: Luiz Henrique Santana", msgs[1]["content"])

    def test_l1_memory_preserves_page1_facts_in_reference_filter(self):
        from app.services.reference_filter import filter_reference_chunks
        mem_chunk = {
            "id": "mem-1",
            "document_id": "doc-1",
            "page_number": 1,
            "content": "Psychology is defined as the scientific study of mind and behavior.",
            "from_memory": True,
        }
        filtered = filter_reference_chunks([mem_chunk])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["content"], mem_chunk["content"])


    def test_author_year_and_three_way_comparison_decomposition(self):
        from app.services.retriever import classify_and_decompose_query
        route_ay = classify_and_decompose_query(
            "So sánh nghiên cứu của Sternberg (2022) và Santana (2023) về phương pháp nghiên cứu tâm lý học."
        )
        self.assertEqual(route_ay["route"], "cross_article_comparison")
        self.assertEqual(route_ay["sub_queries"], ["Sternberg (2022)", "Santana (2023)"])

        route_3way = classify_and_decompose_query(
            "Đối chiếu CBT, DBT và ACT về hiệu quả điều trị trầm cảm."
        )
        self.assertEqual(route_3way["route"], "literature_synthesis")
        self.assertEqual(route_3way["num_targets"], 3)
        self.assertEqual(route_3way["sub_queries"], ["CBT", "DBT", "ACT"])

    def test_rebalance_by_comparison_facets_diversifies_imrad_dimensions(self):
        from app.services.retriever import _rebalance_by_comparison_facets
        chunks = [
            {"id": "1", "content": "Results showed significant correlation r = 0.52, p < 0.01."},
            {"id": "2", "content": "Findings indicated significant effect d = 0.85, p < 0.001."},
            {"id": "3", "content": "Participants included N = 240 adolescents recruited from clinics."},
            {"id": "4", "content": "Measured using PHQ-9 and GAD-7 questionnaires."},
        ]
        rebalanced = _rebalance_by_comparison_facets(chunks)
        facets = [c["comparison_facet"] for c in rebalanced[:3]]
        self.assertEqual(len(set(facets)), 3)

    def test_imrad_classification_and_cross_study_harmonizer(self):
        from app.services.scientific_appraiser import (
            classify_imrad_section,
            harmonize_cross_study_metrics,
            compute_cross_study_concordance,
        )
        intro = classify_imrad_section(
            "Previous work by Smith et al. (2019) and Jones et al. (2021) suggested anxiety increases.",
            page_number=2,
        )
        self.assertEqual(intro["section_code"], "INTRODUCTION")
        self.assertTrue(intro["has_secondary_citations"])

        res = classify_imrad_section(
            "Results showed a significant reduction in depression (r = 0.50, p < 0.01) among participants.",
            page_number=6,
        )
        self.assertEqual(res["section_code"], "RESULTS")

        chunks = [
            {
                "document_id": "d1",
                "doc_filename": "StudyA.pdf",
                "doc_authors": "Sternberg",
                "sub_query_target": "StudyA",
                "page_number": 4,
                "content": "Participants (N = 180) completed BDI-II and results showed r = 0.50, p < 0.01.",
            },
            {
                "document_id": "d2",
                "doc_filename": "StudyB.pdf",
                "doc_authors": "Santana",
                "sub_query_target": "StudyB",
                "page_number": 7,
                "content": "In contrast, 320 patients assessed via PHQ-9 showed OR = 2.45, p < 0.05.",
            },
        ]
        harm = harmonize_cross_study_metrics(chunks)
        self.assertEqual(len(harm["studies"]), 2)
        self.assertIsNone(harm["studies"][0]["sample_n"])
        self.assertEqual(harm["studies"][0]["sample_size_status"], "unverified")
        self.assertEqual(harm["studies"][0]["sample_size_candidates"][0]["value"], 180)
        self.assertIsNone(harm["studies"][0]["harmonized_cohen_d"])
        self.assertIsNone(harm["studies"][0]["effect_value"])
        self.assertEqual(harm["studies"][0]["effect_candidates"][0]["effect_type"], "r")
        self.assertEqual(harm["studies"][0]["effect_candidates"][0]["effect_value"], 0.5)
        self.assertTrue(len(harm["incommensurability_warnings"]) >= 1)

        conc = compute_cross_study_concordance(chunks)
        self.assertEqual(conc["unique_documents_retrieved"], 2)
        self.assertEqual(conc["unique_documents_compared"], 0)
        self.assertEqual(conc["concordance_level"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(conc["concordance_score"])

    def test_comparison_prompt_includes_target_entity_and_source_mapping(self):
        from app.services.generator import build_psychology_prompt
        comp_chunks = [
            {
                "document_id": "d1",
                "doc_filename": "PMC7674837.pdf",
                "doc_title": "Pharmacotherapy vs iCBT for Depression",
                "sub_query_target": "thuốc chống trầm cảm",
                "page_number": 2,
                "content": "Antidepressant medication showed significant symptom reduction at week 8.",
            },
            {
                "document_id": "d2",
                "doc_filename": "PMC4990552.pdf",
                "doc_title": "Internet-based CBT Trial",
                "sub_query_target": "liệu pháp nhận thức hành vi qua máy tính",
                "page_number": 5,
                "content": "Computerized CBT demonstrated sustained remission at 6-month follow-up.",
            },
        ]
        msgs = build_psychology_prompt("So sánh thuốc chống trầm cảm và CBT qua máy tính", comp_chunks, lang="vi")
        user_prompt = msgs[1]["content"]
        self.assertIn("Đối tượng đối chiếu (Target Entity): thuốc chống trầm cảm", user_prompt)
        self.assertIn("Đối tượng đối chiếu (Target Entity): liệu pháp nhận thức hành vi qua máy tính", user_prompt)
        self.assertIn("BẢNG ÁNH XẠ ĐỐI TƯỢNG ĐỐI CHIẾU -> NGUỒN TRÍCH DẪN BẮT BUỘC", user_prompt)
        self.assertIn("[PMC7674837.pdf - Trang 2]", user_prompt)
        self.assertIn("[PMC4990552.pdf - Trang 5]", user_prompt)

        from app.services.retriever import classify_and_decompose_query
        r_doi_voi = classify_and_decompose_query(
            "So sánh tác động của căng thẳng công nghệ (technostress) và áp lực học đường đối với sức khỏe tâm thần: lập bảng đối chiếu."
        )
        self.assertEqual(r_doi_voi["route"], "cross_article_comparison")
        self.assertEqual(r_doi_voi["sub_queries"], ["căng thẳng công nghệ (technostress)", "áp lực học đường"])


if __name__ == '__main__':
    unittest.main()
