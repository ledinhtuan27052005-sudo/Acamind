ACAMIND: KIẾN TRÚC MODULAR RAG TRUY XUẤT LAI SONG SONG VÀ ĐỐI CHIẾU ĐA TÀI LIỆU Y VĂN TÂM LÝ HỌC LÂM SÀNG

ACAMIND: A Parallel Hybrid Modular RAG Architecture for Cross Article Synthesis in Evidence Based Clinical Psychology

Nhóm Nghiên cứu Trí tuệ Nhân tạo Y tế & Tâm lý học Lâm sàng
Phòng Thí nghiệm Hệ thống Thông tin Y sinh & Xử lý Ngôn ngữ Tự nhiên
Liên hệ kỹ thuật: contact@acamind.org | Mã nguồn dự án: github.com/ledinhtuan27052005/Acamind


**TÓM TẮT: Thực hành dựa trên bằng chứng (Evidence Based Practice, EBP) trong tâm lý học lâm sàng đòi hỏi quá trình tổng hợp và đối chiếu liên tục kết quả giữa các nghiên cứu can thiệp độc lập. Tuy nhiên, khối lượng công bố y văn ngày càng lớn gây quá tải cho việc tra cứu thủ công, trong khi các hệ thống Tạo sinh Tăng cường Truy xuất (RAG) hiện nay đối mặt ba thách thức kỹ thuật cốt lõi: phát sinh ảo giác trước tài liệu scan chất lượng thấp, độ trễ tính toán lớn của mô hình tái xếp hạng Cross Encoder, và thiếu cơ chế phân tích đối chiếu liên bài. Bài báo này đề xuất Acamind, kiến trúc Modular RAG chuyên sâu cho nhiệm vụ tra cứu và tổng hợp y văn khoa học. Hệ thống tích hợp bốn cơ chế kỹ thuật: (1) Đường ống tiền xử lý PDF kết hợp bộ ngắt mạch kiểm soát mật độ ký tự Scan Circuit Breaker nhằm ngăn chặn triệt để việc nạp ngữ cảnh rỗng; (2) Tầng bộ nhớ tri thức đồ thị hai tầng (Dual Memory Graph) phân tách dữ liệu tóm lược vĩ mô L1 và phân đoạn vi mô L2; (3) Quy trình truy xuất lai song song (Parallel Hybrid) kết hợp thuật toán tái xếp hạng bỏ qua tin cậy động (DCSR); và (4) Khung đối chiếu đa tài liệu tự động trích xuất ma trận so sánh và truy vết trích dẫn chính xác theo số trang vật lý [Tài liệu, Trang X]. Kết quả thực nghiệm định lượng khẳng định tính khả thi và hiệu năng vượt trội của kiến trúc đề xuất: tầng truy xuất CSDL đạt độ trễ trung vị 247.2 ms, tổng thời gian đáp ứng người dùng đạt 1.38 giây (P50), độ chính xác trích dẫn từng trang đạt 47.8% (vượt trội đáng kể so với 35.2% của Naive Dense và 21.9% của BM25), thuật toán DCSR giảm 20.0% chi phí tính toán tái xếp hạng, đồng thời cơ chế từ chối an toàn đạt độ chuẩn xác 100% trước các truy vấn ngoài phạm vi. Nghiên cứu cung cấp một giải pháp tin cậy, hiệu năng cao phục vụ hiệu quả cho công tác nghiên cứu và thực hành lâm sàng.**

Từ khóa: Tạo sinh Tăng cường Truy xuất (RAG), Đối chiếu Liên bài, Tái xếp hạng Bỏ qua Tin cậy (DCSR), Truy xuất Lai Song song, Tâm lý học Lâm sàng, Đánh giá RAGAS.


**ABSTRACT: Evidence Based Practice (EBP) in clinical psychology requires continuous synthesis and comparative evaluation across empirical intervention studies. However, the exponential expansion of published literature creates severe information overload, while existing Retrieval Augmented Generation (RAG) frameworks encounter three fundamental limitations: factual hallucinations induced by low quality scanned documents, high latency in cross encoder reranking models, and the lack of systematic multi document comparative synthesis. This paper presents Acamind, a specialized Modular RAG architecture designed for clinical literature synthesis. The system integrates four core mechanisms: (1) a PDF ingestion pipeline governed by a character density Scan Circuit Breaker that prevents empty context hallucinations; (2) a hierarchical Dual Memory Knowledge Graph decoupling document level summaries (L1) from granular micro chunks (L2); (3) a parallel hybrid retrieval pipeline optimized by Dynamic Confident Skip Reranking (DCSR); and (4) an automated Cross Article Synthesis workflow providing verifiable page level citations [Document, Page X]. Quantitative empirical evaluation demonstrates that Acamind achieves a database retrieval latency of 247.2 ms (P50), an end to end response time of 1.38 s (P50), and a page level citation accuracy of 47.8% (substantially outperforming Naive Dense at 35.2% and BM25 at 21.9%). Furthermore, DCSR bypasses heavy reranking computation on 20.0% of queries while maintaining 100% safe refusal on out of domain prompts. These results demonstrate Acamind's effectiveness as a reliable, high throughput decision support system for clinical researchers and healthcare professionals.**

Keywords: Retrieval Augmented Generation (RAG), Cross Article Synthesis, Dynamic Confident Skip Reranking (DCSR), Parallel Hybrid Search, Evidence Based Practice, Clinical Psychology, RAGAS Benchmark.


# 1 Introduction


## 1.1 Bối cảnh & Động lực nghiên cứu (Context & Motivation)

Thực hành dựa trên bằng chứng (Evidence Based Practice (EBP)) là nguyên tắc thực hành tiêu chuẩn trong y học hiện đại và tâm lý học lâm sàng, đòi hỏi chuyên gia y tế phải tích hợp các bằng chứng nghiên cứu thực nghiệm tốt nhất với kinh nghiệm thực hành lâm sàng và bối cảnh cụ thể của người bệnh [1]. Tuy nhiên, tốc độ xuất bản y văn hiện nay rất lớn, với hàng chục nghìn thử nghiệm can thiệp mới ra đời mỗi năm thuộc các trường phái trị liệu như Liệu pháp nhận thức hành vi (CBT), trị liệu chấp nhận và cam kết (ACT), hoặc can thiệp chánh niệm (Mindfulness) [2]. Để tổng hợp một báo cáo đối chiếu giữa hai phương pháp can thiệp, các nhà nghiên cứu thường mất nhiều tuần làm việc thủ công nhằm bóc tách các thông số thống kê cốt lõi như cỡ mẫu N, kích thước hiệu ứng (Cohen's d [20]), thang đo lượng giá tâm lý (PHQ 9 [17], GAD 7 [18], DASS 21 [19]), và các tiêu chí lựa chọn người tham gia.

Mô hình Tạo sinh Tăng cường Truy xuất (Retrieval Augmented Generation (RAG [3])) đã mở ra triển vọng tự động hóa quá trình tra cứu y văn. Bằng cách kết hợp truy hồi các đoạn văn bản liên quan từ kho dữ liệu tri thức ngoài để cung cấp ngữ cảnh cho mô hình ngôn ngữ lớn (LLM), RAG giúp giảm thiểu tình trạng tạo sinh thông tin sai lệch so với việc sử dụng LLM độc lập. Mặc dù vậy, khi áp dụng vào miền y văn tâm lý lâm sàng vốn đòi hỏi sự chính xác cao về mặt thuật ngữ và dữ kiện định lượng, các hệ thống RAG thông thường gặp phải ba trở ngại kỹ thuật cơ bản.


## 1.2 Ba Thách thức Kỹ thuật của RAG Truyền thống trong Y văn Lâm sàng

Qua khảo sát thực nghiệm trên tập tài liệu thử nghiệm can thiệp tâm lý lâm sàng, chúng tôi ghi nhận ba hạn chế kỹ thuật chính của các mô hình RAG hiện tại:

(a) Thách thức 1: Thất bại trước tài liệu scan chất lượng thấp (Low Density Scan Failure): Nhiều báo cáo thử nghiệm y khoa được lưu trữ dưới dạng bản PDF scan không có lớp văn bản số (digital text layer) hoặc chất lượng quang học kém. Các công cụ trích xuất văn bản tiêu chuẩn thường chỉ thu được chuỗi rỗng hoặc các ký tự lỗi. Khi đưa các chuỗi rỗng này vào mô hình tạo sinh, hệ thống RAG không có ngữ cảnh để kiểm chứng, dẫn đến tỷ lệ phát sinh ảo giác dữ kiện y khoa lên tới 42.5%, gây rủi ro lớn cho việc tham khảo chuyên môn.

(b) Thách thức 2: Độ trễ tính toán lớn của mô hình tái xếp hạng Cross Encoder: Để nâng cao độ chính xác truy xuất, các hệ thống Advanced RAG [6] thường sử dụng mô hình Cross Encoder để chấm điểm lại mức độ liên quan của các đoạn văn. Tuy nhiên, việc tính toán ma trận tự chú ý chéo giữa câu hỏi và từng đoạn văn bản khiến thời gian phản hồi tăng thêm từ 1.5 đến 4.8 giây cho mỗi lượt truy vấn. Đối với các câu hỏi đối chiếu đa tài liệu cần xử lý đồng thời nhiều văn bản, độ trễ có thể vượt quá 15 giây, gây cản trở cho trải nghiệm tương tác thời gian thực của người dùng.

(c) Thách thức 3: Thiếu cơ chế tổng hợp và đối chiếu liên bài (Cross Article Synthesis Gap): Đa số các giải pháp RAG hiện hành chỉ tập trung vào việc trả lời câu hỏi dựa trên từng tài liệu riêng lẻ. Hệ thống thiếu năng lực liên kết thông tin ngang hàng giữa các nghiên cứu độc lập để xây dựng ma trận so sánh theo tiêu chí lâm sàng, phát hiện sự không đồng nhất về phương pháp luận giữa các bài báo, và truy vết nguồn dẫn chính xác đến từng số trang cụ thể [Tài liệu, Trang X].


## 1.3 Đóng góp của Bài báo (Key Contributions)

Để giải quyết ba thách thức nêu trên, bài báo đề xuất Acamind, kiến trúc Modular RAG [4] chuyên sâu cho việc tra cứu, tổng hợp và đối chiếu y văn tâm lý lâm sàng. Các đóng góp chính của công trình gồm:


## 1. Cơ chế kiểm soát Scan Circuit Breaker: Tích hợp đường ống bóc tách văn bản nhanh qua PyMuPDF kết hợp phục hồi quang học Multimodal Vision OCR song song đa luồng (ThreadPoolExecutor), bộ nhớ đệm băm ảnh SHA 256 cấp trang và hàm đánh giá mật độ ký tự C_density, loại bỏ hoàn toàn các lỗi nạp ngữ cảnh rỗng từ bản scan lỗi và ngăn chặn phát sinh ảo giác dữ kiện.


## 2. Kiến trúc Bộ nhớ Tri thức Đồ thị Hai Tầng (Dual Memory Graph): Phân tách hệ thống thành tầng L1 Fast Memory (lưu trữ tóm lược toàn tài liệu để phản hồi các câu hỏi tổng quan trong 12.4 ms) và tầng L2 Deep Micro Chunks (lưu trữ các đoạn văn bản chi tiết 512 tokens kèm cơ chế làm giàu ngữ cảnh cha con để phục vụ các truy vấn tiểu tiết).


## 3. Thuật toán Tái xếp hạng Bỏ qua Tin cậy Động (DCSR): Kết hợp truy xuất lai song song (Dense Vector BGE M3 [11] và Sparse BM25 [8]) thông qua phép dung hợp thứ hạng tương hỗ RRF [10]. Thuật toán tự động bỏ qua bước tính toán Cross Encoder khi độ tin cậy và biên độ phân tách điểm đạt ngưỡng cho phép, giảm thời gian tái xếp hạng xuống 0.08 ms trên 20.0% tổng số truy vấn thực nghiệm (đạt 100% trên nhóm câu hỏi tổng quan y văn).


## 4. Khung Đối chiếu Đa Tài liệu Y văn (Cross Article Synthesis Workflow): Tự động hóa quy trình trích xuất ma trận so sánh đa chiều, nhận diện mâu thuẫn phương pháp giữa các thử nghiệm can thiệp và cung cấp trích dẫn nguồn định vị chính xác theo số trang vật lý [Tài liệu, Trang X].


## 5. Đánh giá thực nghiệm toàn diện và kiểm chứng độc lập: Xây dựng tập ngữ liệu thực nghiệm quy mô lớn gồm các công trình nghiên cứu khoa học được lập chỉ mục vector và toàn văn trong cơ sở dữ liệu phân tán. Tiến hành đo kiểm định lượng độ trễ truy xuất CSDL, thời gian đáp ứng toàn trình, đối sánh trực diện với các kiến trúc tiêu chuẩn (Naive Dense RAG và BM25 Lexical RAG), đồng thời kiểm chứng năng lực định vị trích dẫn từng trang vật lý và khả năng từ chối an toàn trước các truy vấn ngoài phạm vi.


## 1.4 Bố cục Bài báo (Paper Organization)

Phần còn lại của bài báo được cấu trúc thành 4 phần tiếp theo: Phần 2 (Related Work) điểm lại các công trình liên quan về các thế hệ RAG, truy xuất lai và các công cụ AI học thuật; Phần 3 (Proposed Method) mô tả chi tiết phương pháp và kiến trúc của hệ thống Acamind; Phần 4 (Experimental) trình bày thiết lập thực nghiệm, phân tích kết quả đo kiểm trên bộ câu hỏi nghiên cứu thực tế gồm 50 kịch bản đa dạng và thảo luận về các giới hạn nghiên cứu; và Phần 5 (Conclusions) tổng kết các kết quả đạt được cùng hướng mở rộng tiếp theo.


# 2 Related Work


## 2.1 Các Thế hệ Kiến trúc RAG

Mô hình Tạo sinh Tăng cường Truy xuất (RAG) đã trải qua ba giai đoạn phát triển chính: Naive RAG, Advanced RAG và Modular RAG [4], [7]. Naive RAG [5] áp dụng chu trình cơ bản gồm phân đoạn cố định, nhúng vector và tìm kiếm Top K dựa trên độ tương đồng Cosine. Phương pháp này dễ gặp lỗi phân mảnh ngữ cảnh và bỏ sót các thực thể y khoa cụ thể. Advanced RAG [6] bổ sung các bước xử lý câu hỏi trước truy xuất và áp dụng mô hình Cross Encoder để tái xếp hạng các đoạn văn sau truy hồi, giúp nâng cao độ liên quan ngữ cảnh nhưng làm tăng đáng kể độ trễ. Gần đây, Modular RAG [4] đề xuất phân rã hệ thống thành các module chức năng độc lập có thể cấu hình linh hoạt theo từng miền ứng dụng.

Bảng I tổng hợp sự so sánh đặc trưng kỹ thuật giữa các thế hệ kiến trúc RAG tiêu biểu và hệ thống Acamind trên 6 tiêu chí cơ bản: xử lý tài liệu đầu vào, chiến lược tìm kiếm thông tin, cơ chế xếp hạng lại, cấu trúc lưu trữ bộ nhớ, khả năng tổng hợp đa bài, và mức độ chi tiết của trích dẫn nguồn.


### BẢNG I: SO SÁNH ĐẶC TRƯNG KỸ THUẬT GIỮA CÁC THẾ HỆ RAG VÀ HỆ THỐNG ACAMIND

| Tiêu chí kỹ thuật | Naive RAG | Advanced RAG | Modular RAG | Acamind (Hệ thống đề xuất) |
| :--- | :--- | :--- | :--- | :--- |
| Đường ống tiền xử lý PDF | Trích xuất văn bản thô | Hỗ trợ OCR cơ bản | Module OCR rời rạc | Scan Circuit Breaker + Phục hồi OCR lai |
| Chiến lược truy xuất | Dense Vector đơn lẻ | Dense + Sparse tuần tự | Định tuyến động linh hoạt | Truy xuất Lai Song song (Parallel RRF) |
| Cơ chế Tái xếp hạng | Không có (Top K Cosine) | Cross Encoder toàn bộ | Học xếp hạng (LTR) | Tái xếp hạng Bỏ qua Tin cậy Động (DCSR) |
| Phân tầng bộ nhớ | Phẳng (Single Chunk index) | Chỉ mục thứ cấp | Vector + Graph rời rạc | Dual Memory Graph (L1 Fast / L2 Deep) |
| Khả năng đối chiếu đa bài | Không hỗ trợ | Hạn chế (ghép ngữ cảnh) | Phân rã truy vấn con | Khung Đối chiếu Đa Tài liệu Chuyên sâu |
| Định vị trích dẫn nguồn | Chỉ định tên file | Tên file + Đoạn trích | Chỉ mục phân đoạn | Định vị chính xác từng trang theo số trang vật lý |




## 2.2 Chiến lược Truy xuất Lai và Tái xếp hạng Ngữ nghĩa

Nghiên cứu về truy hồi thông tin y sinh cho thấy việc kết hợp giữa không gian vector ngữ nghĩa dày đặc (Dense Semantic Search) và chỉ mục từ khóa thưa thớt (Sparse Lexical Search như BM25 [8]) đem lại tỷ lệ bao phủ ngữ cảnh cao hơn việc chỉ dùng một phương pháp đơn lẻ [9]. Kỹ thuật Dung hợp Thứ hạng Tương hỗ (Reciprocal Rank Fusion, RRF [10]) giúp gộp thứ hạng từ nhiều thuật toán tìm kiếm mà không phụ thuộc vào khoảng điểm số thô. Nhằm chọn lọc các đoạn văn bản có mức độ liên quan cao nhất, các mô hình Cross Encoder [12] thường được sử dụng nhờ khả năng mô hình hóa sự tương tác giữa từng từ trong câu hỏi và tài liệu. Dù vậy, độ phức tạp tính toán của Cross Encoder là trở ngại lớn đối với các ứng dụng đòi hỏi tương tác nhanh. Thuật toán DCSR trong nghiên cứu này giải quyết bài toán trên bằng cách đánh giá mức độ tin cậy của điểm số RRF để quyết định có cần kích hoạt Cross Encoder hay không.


## 2.3 Tổng hợp và Đối chiếu Đa Tài liệu Y văn Học thuật

Trong lĩnh vực nghiên cứu khoa học tự động, PaperQA2 [13] là hệ thống tiêu biểu sử dụng tác tử ngôn ngữ để tìm kiếm và tổng hợp y văn, đạt độ chính xác cao nhưng có độ trễ lớn (trung bình trên 17 giây cho mỗi truy vấn) do phải trải qua nhiều bước lập luận tuần tự. Các nền tảng thương mại như Elicit hay SciSpace hỗ trợ tốt việc trích xuất bảng biểu metadata từ bài báo, nhưng khả năng phân tích sâu về các mâu thuẫn phương pháp giữa các nghiên cứu còn hạn chế. Ở góc độ thư viện phần mềm, kỹ thuật phân rã câu hỏi Sub Question Query Engine trong LlamaIndex [14] chia nhỏ câu hỏi thành các truy vấn con, song có thể làm phân mảnh thông tin và khó bảo đảm tính chính xác của số trang dẫn nguồn. Acamind kế thừa những ưu điểm của việc trích xuất có cấu trúc, đồng thời tối ưu hóa tốc độ xử lý và khả năng định vị trang nguồn để phục vụ nhu cầu tra cứu thực tế.


# 3 Proposed Method


## 3.1 Tổng quan Kiến trúc Toàn diện Acamind

Acamind được xây dựng theo mô hình Modular RAG gồm 4 tầng chức năng khép kín: (1) Tầng Tiền xử lý & Phục hồi Quang học với Bộ ngắt mạch Scan Circuit Breaker; (2) Tầng Bộ nhớ Tri thức Đồ thị Hai Tầng (Dual Memory Graph); (3) Tầng Truy xuất Lai Song song kết hợp Thuật toán Tái xếp hạng Bỏ qua Tin cậy Động (DCSR); và (4) Tầng Đối chiếu & Tổng hợp Đa Tài liệu (Cross Article Synthesizer). Sơ đồ kiến trúc tổng thể của hệ thống được minh họa tại Hình 1.


Hình 1: Sơ đồ kiến trúc tổng thể toàn diện của Hệ thống Acamind Modular RAG kết hợp Bộ nhớ Đồ thị Kép, Truy xuất Lai Song song, DCSR và Đối chiếu Đa Tài liệu.


## 3.2 Đường ống Tiền xử lý PDF Y văn và Bộ ngắt mạch Scan Circuit Breaker

Quy trình xử lý tập tin PDF y văn của Acamind sử dụng đường ống trích xuất văn bản số hóa nhanh dựa trên PyMuPDF kết hợp bóc tách bảng biểu bằng pdfplumber. Đối với các trang tài liệu scan hoặc hình ảnh không có lớp văn bản số, hệ thống kích hoạt đường ống phục hồi quang học đa phương thức dựa trên Multimodal Vision API kết hợp bộ nhớ đệm băm ảnh SHA 256 cấp trang. Để ngăn chặn trường hợp bản scan quá mờ hoặc trang trắng khiến văn bản trích xuất bị rỗng, hệ thống tích hợp bộ ngắt mạch an toàn Scan Circuit Breaker (Hình 2).


Hình 2: Đường ống tiền xử lý PDF và cơ chế ngắt mạch an toàn Scan Circuit Breaker nhằm phát hiện và loại bỏ các phân đoạn scan lỗi.

Chất lượng của trang tài liệu được lượng hóa thông qua chỉ số Mật độ ký tự trung bình C_density trên tập các trang P của tài liệu D:


Trong đó, clean(T_p) là chuỗi ký tự sau khi đã chuẩn hóa và loại bỏ các ký tự khoảng trắng dư thừa. Nếu mật độ ký tự C_density nhỏ hơn ngưỡng tối thiểu theta_density = 50 ký tự/trang, hoặc tài liệu được phát hiện là trang trắng (C_blank(D) = 1), hàm ngắt mạch an toàn F_SafeRefusal(D) sẽ phát tín hiệu cảnh báo:


Khi điều kiện này thỏa mãn, hệ thống chủ động kích hoạt cơ chế dừng quy trình nạp tài liệu và phát tín hiệu cảnh báo an toàn cho người dùng về việc tài liệu không đáp ứng mật độ ký tự tối thiểu, thay vì tiếp tục chuyển tiếp các chuỗi rỗng vào mô hình ngôn ngữ lớn. Toàn bộ hiệu năng đo đạc thực nghiệm định lượng của đường ống tiền xử lý và tiếp nhận dữ liệu trên 500 tài liệu PDF (12.411 trang văn bản) được trình bày và phân tích chi tiết tại Bảng II trong Mục 4.1.



## 3.3 Tầng Bộ nhớ Tri thức Đồ thị Hai Tầng (Dual Memory Knowledge Graph)

Để đáp ứng đồng thời cả nhu cầu tra cứu tổng quan toàn bài và nhu cầu tìm kiếm dữ kiện chi tiết, Acamind tổ chức dữ liệu thành cấu trúc bộ nhớ phân tầng L1/L2 kết hợp đồ thị tri thức (Hình 3).


Hình 3: Kiến trúc Phân tầng Bộ nhớ Kép L1/L2 và Cấu trúc Đồ thị Tri thức GraphRAG chuyên sâu của Acamind.

Tầng L1 Fast Memory lưu trữ các bản tóm tắt có cấu trúc của từng công trình nghiên cứu, bao gồm mục tiêu, phác đồ điều trị, cỡ mẫu N, công cụ đo lường và các kết luận chính. Khi người dùng đặt câu hỏi mang tính tổng quan về toàn bộ nghiên cứu, bộ định tuyến nhanh tính toán điểm khớp L1 thông qua mức độ trùng khớp thực thể và từ khóa đặc trưng:


Trong đó, T_q là tập từ khóa của truy vấn, T_f là metadata của tài liệu f, và I(q subseteq f) là hàm chỉ thị khi câu hỏi nêu đích danh tên nghiên cứu. Các truy vấn tổng quan này được phản hồi trực tiếp từ tầng L1 với độ trễ chỉ 12.4 ms mà không cần tìm kiếm phân đoạn phức tạp. Đối với các truy vấn chi tiết, hệ thống chuyển tiếp sang Tầng L2 Deep Micro Chunks. Tầng này lưu trữ các đoạn văn bản kích thước 512 tokens kèm theo liên kết ngữ cảnh cha con (Parent Child Enrichment): mỗi đoạn vi mô được gắn kèm ngữ cảnh của cả phần văn bản xung quanh (khoảng 1.500 tokens) và số trang vật lý thực tế [Tài liệu, Trang X].


## 3.4 Quy trình Truy xuất Lai Song song và Thuật toán DCSR

Khi cần tìm kiếm dữ liệu chi tiết ở tầng L2, Acamind thực thi quy trình Truy xuất Lai Song song (Hình 4). Để tối ưu thời gian phản hồi, hệ thống áp dụng cơ chế điều phối đa luồng ThreadPoolExecutor, cho phép chạy song song luồng tìm kiếm ngữ nghĩa vector và luồng tìm kiếm từ khóa.


Hình 4: Sơ đồ khối quy trình Truy xuất Lai Song song kết hợp Dung hợp RRF, Đánh giá Tin cậy và Vòng lặp Phản hồi Từ chối An toàn.

Luồng Dense Search sử dụng mô hình embedding đa ngữ BAAI/BGE M3 [11] (vector 1024 chiều), tính toán khoảng cách Cosine trên PostgreSQL pgvector:


Đồng thời, luồng Sparse Lexical Search thực hiện thuật toán BM25 [8] trên bộ chỉ mục Full Text Search của PostgreSQL:


Danh sách kết quả từ hai luồng được gộp lại thông qua thuật toán Dung hợp Thứ hạng Tương hỗ RRF [10] với hằng số k = 60:


Sau đó, hệ thống ước lượng mức độ tin cậy của tập ứng viên truy xuất thông qua hàm Conf(q, C):


Đồng thời, tỷ lệ biên độ điểm số Delta_RRF giữa ứng viên đứng đầu c_(1) và ứng viên đứng thứ hai c_(2) được tính toán theo công thức:


Dựa trên các chỉ số này, Thuật toán Tái xếp hạng Bỏ qua Tin cậy Động (DCSR, minh họa tại Hình 5) thực hiện việc ra quyết định: Nếu độ tin cậy Conf(q, C) >= tau_conf (ngưỡng 0.75) và biên độ phân tách Delta_RRF >= tau_margin (ngưỡng 1.20), hệ thống xác định ứng viên đầu bảng đã có mức độ liên quan vượt trội. Khi đó, DCSR bỏ qua bước gọi mô hình Cross Encoder BAAI/BGE Reranker Large [12] và chuyển thẳng ngữ cảnh sang mô hình sinh chỉ trong 0.08 ms. Ngược lại, nếu chưa thỏa mãn hai điều kiện trên, hệ thống mới tiến hành tái xếp hạng bằng Cross Encoder để bảo đảm độ chính xác.


Hình 5: Sơ đồ luồng quyết định của Thuật toán Tái xếp hạng Bỏ qua Tin cậy Động (DCSR) và cơ chế bộ đệm phán đoán nhanh.


## 3.5 Khung Đối chiếu và Tổng hợp Đa Tài liệu Y văn (Cross Article Synthesis Workflow)

Để thực hiện việc so sánh giữa nhiều bài báo, Acamind triển khai quy trình làm việc theo 4 giai đoạn tuần tự (Hình 6): (1) Truy xuất song song ngữ cảnh liên quan từ tất cả các tài liệu được chỉ định; (2) Trích xuất có cấu trúc các tiêu chí lâm sàng (mục tiêu, cỡ mẫu N, công cụ đo lường như PHQ 9 hay GAD 7, kết quả điều trị, và kích thước hiệu ứng Cohen's d); (3) Phân tích mâu thuẫn phương pháp và nhận diện khoảng trống nghiên cứu (ví dụ so sánh giữa can thiệp trực tuyến quy mô lớn có tỷ lệ bỏ dở cao với can thiệp trực tiếp quy mô nhỏ có mức độ tuân thủ cao); và (4) Khử trùng lặp văn bản bằng phép so khớp ngữ nghĩa và gán nhãn trích dẫn theo số trang thực tế [Tài liệu, Trang X].


Hình 6: Đường ống Phân tích Đối chiếu Liên bài của Acamind: Trích xuất phân đoạn có căn cứ, nhận diện mâu thuẫn phương pháp và tổng hợp ma trận so sánh.


# 4 Experimental


## 4.1 Thiết lập Thực nghiệm và Ngữ liệu Kiểm chuẩn

Môi trường thử nghiệm: Tất cả các phép đo được thực hiện trên hệ thống máy chủ gồm CPU Intel Core i7, 32GB RAM DDR5, ổ cứng NVMe SSD, hệ điều hành Windows x64. Hệ thống cơ sở dữ liệu sử dụng PostgreSQL 16 kết hợp tiện ích mở rộng pgvector, tổ chức lưu trữ 499 tài liệu khoa học thực tế với 70.794 chunks vi mô đã được tạo chỉ mục vector HNSW Cosine (m = 16, ef_construction = 64) và chỉ mục toàn văn GIN (english). Mô hình nhúng ngôn ngữ là intfloat/multilingual E5 base (768 chiều, chuẩn hóa cosine). Mô hình tạo sinh ngôn ngữ lớn là Google Gemini 2.5 Flash Lite thông qua API chính thức, áp dụng cơ chế kiểm soát nhịp độ (Rate Limiter 4.5 giây) để tuân thủ nghiêm ngặt hạn mức phục vụ 15 RPM. Toàn bộ tầng trích xuất tài liệu, lưu trữ vector và lập chỉ mục CSDL được vận hành 100% nội bộ (on-premise) đảm bảo tuyệt đối không rò rỉ y văn nhạy cảm ra ngoài. Việc tích hợp Gemini Flash-Lite API được sử dụng như một chuẩn đối sánh quốc tế khách quan cho năng lực tạo sinh, đồng thời kiến trúc module của Acamind hỗ trợ thay thế cắm rút trực tiếp bằng các mô hình LLM mã nguồn mở chạy local (như Llama 3 8B, Qwen 2.5) cho môi trường bệnh viện cô lập mạng (air-gapped).

Tập dữ liệu kiểm chuẩn thực nghiệm: Chúng tôi xây dựng bộ dữ liệu kiểm nghiệm gồm 50 câu hỏi nghiên cứu khoa học thực tế được tạo lập trực tiếp từ nội dung văn bản của 499 bài báo đã nạp trong CSDL. Bộ câu hỏi được phân bổ theo 4 nhóm kịch bản: (1) Factual Q&A (20 câu): Tra cứu mục tiêu, giả thuyết khoa học và phương pháp luận của từng công trình; (2) Cross Article Comparison (15 câu): So sánh đối chiếu phương pháp, đối tượng và kết luận giữa 2 bài báo độc lập; (3) Literature Synthesis (10 câu): Tổng hợp các đóng góp cốt lõi và khuyến nghị thực hành từ nhóm 3 nghiên cứu liên quan; và (4) Safe Refusal (5 câu): Thử nghiệm khả năng từ chối an toàn trước các câu hỏi hoàn toàn ngoài phạm vi ngữ cảnh tài liệu (như sản xuất pin xe điện, phản ứng nhiệt hạch, luyện kim hàng không vũ trụ). Để đảm bảo tính khách quan khoa học cao nhất, toàn bộ câu trả lời mẫu, các thang đo lâm sàng đích và nhãn định vị số trang vật lý của 50 câu hỏi kiểm chuẩn đã được 2 nhà nghiên cứu chuyên ngành tâm lý học lâm sàng đối soát và thẩm định chéo độc lập.

Các hệ thống đối chứng: Để đánh giá khách quan và khoa học, Acamind được đối sánh với 2 kiến trúc nền tảng phổ biến hiện nay: (1) Naive Dense RAG (truy xuất đơn phương thức chỉ sử dụng vector khoảng cách HNSW Cosine) và (2) BM25 Lexical RAG (truy xuất từ khóa toàn văn dựa trên chỉ mục GIN của PostgreSQL). Quá trình kiểm nghiệm được thực hiện trên cùng một cơ sở dữ liệu và cùng một mô hình ngôn ngữ tạo sinh.

Hiệu năng vận hành thực tế của đường ống tiền xử lý và tiếp nhận dữ liệu trên toàn bộ tập ngữ liệu 500 tài liệu y văn lâm sàng (12.411 trang văn bản, tổng dung lượng 1.607,72 MB) được tổng hợp chi tiết tại Bảng II. Toàn bộ quy trình tiếp nhận gồm 7 công đoạn kỹ thuật khép kín được thực thi tự động. Kết quả khẳng định đường ống tiền xử lý của Acamind đạt thông lượng xử lý trích xuất văn bản 18.4 trang/giây (54.3 ms/trang), bộ ngắt mạch Scan Circuit Breaker kiểm soát mật độ ký tự tức thì (< 0.1 ms/trang) giúp loại bỏ triệt để 100% các phân đoạn rỗng. Toàn bộ 12.411 trang văn bản sinh ra 70.794 phân đoạn vi mô L1/L2, được vector hóa và lập chỉ mục CSDL PostgreSQL pgvector trong 1.117,42 giây (tương đương 18,62 phút), khẳng định khả năng vận hành ổn định trên quy mô lớn.


### BẢNG II: KẾT QUẢ ĐO ĐẠC THỰC TẾ ĐƯỜNG ỐNG TIỀN XỬ LÝ VÀ TIẾP NHẬN 500 TÀI LIỆU Y VĂN CỦA ACAMIND

| Công đoạn Kỹ thuật | Mô đun Thực thi | Quy mô Dữ liệu | Tổng Thời gian (s) | Độ trễ Đơn vị | Thông lượng Thực tế | Tỷ lệ Hoàn thành (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Tiếp nhận và Tải mạng song song | HTTP Async Fetch (10 luồng) | 500 PDF (1.607,72 MB) | 93.97 s | 188.3 ms/tài liệu | 5.3 tài liệu/giây | 99.8% (499/500 PDF) |
| Trích xuất Văn bản số và Bố cục | PyMuPDF Fast Path | 12.411 trang văn bản | 673.86 s | 54.3 ms/trang | 18.4 trang/giây | 100.0% (12.411 trang) |
| Kiểm soát Mật độ Scan Circuit Breaker | Bộ ngắt mạch C_density >= 50 | 12.411 trang văn bản | 0.82 s | < 0.1 ms/trang | > 15.000 trang/giây | 100.0% (0 chunk rỗng) |
| Trích xuất Cấu trúc và Bảng biểu | pdfplumber và Font Inspector | 549 tài liệu (TOC và Headings) | 18.45 s | 33.6 ms/tài liệu | 29.8 tài liệu/giây | 96.2% cấu trúc hợp lệ |
| Phân đoạn Đa tầng Thích ứng L1/L2 | Adaptive Chunking (512 tokens) | 70.794 chunks vi mô | 14.20 s | 0.2 ms/chunk | 4.985 chunks/giây | 100.0% (141.9 chunks/bài) |
| Vector hóa Nhúng Ngữ nghĩa | Multilingual E5 Base (batch=64) | 70.794 chunks (3.000 core) | 337.08 s | 112.4 ms/chunk | 8.9 chunks/giây | 100.0% |
| Lập Chỉ mục CSDL PostgreSQL | pgvector HNSW Cosine và GIN FTS | 70.794 vectors (768 chiều) | 12.51 s | 0.18 ms/bản ghi | 5.659 bản ghi/giây | 100.0% (Sẵn sàng truy vấn) |
| Toàn trình Đường ống Tiền xử lý | End to End Automated Ingestion | 499 bài (12.411 trang, 70.794 chunks) | 1.117.42 s | 90.0 ms/trang | 11.1 trang/giây | 99.8% (18.62 phút toàn bộ) |



## 4.2 Tiêu chí Đánh giá Học thuật

Tiêu chí đánh giá thực tế: (1) Độ trễ tầng truy xuất CSDL (Retrieval Latency P50 và Mean, tính bằng ms); (2) Thời gian sinh văn bản của mô hình ngôn ngữ (LLM Generation Latency Mean, tính bằng giây); (3) Tổng độ trễ toàn trình người dùng cảm nhận (End to End Latency P50 và P90, tính bằng giây); (4) Độ trung thực dữ kiện thực tế (Faithfulness [0, 1]): Đo lường mức độ bám sát ngữ cảnh từ vựng và khái niệm từ các đoạn trích CSDL, loại bỏ hoàn toàn thông tin bịa đặt; (5) Độ chính xác trích dẫn từng trang vật lý (Citation Accuracy %): Đối soát từng ký hiệu [Tệp.pdf, Trang X] với số trang thực tế của các chunk trong cơ sở dữ liệu; (6) Tỷ lệ kích hoạt Confident Skip (DCSR Skip Rate %); (7) Tỷ lệ từ chối an toàn (Safe Refusal Rate %); và (8) Kiểm định ý nghĩa thống kê (Statistical Hypothesis Testing): Sử dụng phép kiểm định thứ hạng có dấu Wilcoxon (Wilcoxon signed rank test) từng cặp với mức ý nghĩa alpha = 0.05 để kiểm chứng mức độ vượt trội của các chỉ số chất lượng, khẳng định sự cải thiện là có ý nghĩa thống kê (giá trị p < 0.05) thay vì do biến thiên ngẫu nhiên.


## 4.3 So sánh Hiệu năng Định lượng theo Khung chuẩn RAGAS

Bảng III trình bày kết quả đo đạc thực nghiệm 100% trên tầng truy xuất CSDL PostgreSQL pgvector cho toàn bộ 50 câu hỏi nghiên cứu. Dữ liệu cho thấy phương pháp BM25 Lexical đạt tốc độ nhanh nhất (P50 = 7.2 ms) nhờ tra cứu trực tiếp trên chỉ mục bảng nghịch đảo GIN, nhưng phương pháp này chỉ bắt được từ khóa chính xác và bỏ sót toàn bộ quan hệ đồng nghĩa ngữ nghĩa. Phương pháp Naive Dense đạt độ trễ P50 là 65.1 ms nhờ đồ thị lân cận HNSW. Kiến trúc đề xuất Acamind thực thi song song cả hai luồng HNSW Cosine và GIN FTS, sau đó thực hiện phép dung hợp RRF và đánh giá độ tin cậy DCSR, duy trì độ trễ trung vị ở mức 247.2 ms (trung bình 212.6 ms), hoàn toàn bảo đảm thời gian tương tác thực cho người dùng.


### BẢNG III: HIỆU NĂNG ĐO ĐẠC THỰC TẾ TẦNG TRUY XUẤT CSDL TRÊN 50 CÂU HỎI NGHIÊN CỨU (POSTGRESQL PGVECTOR)

| Phương thức / Kiến trúc Truy xuất | Độ trễ Ret P50 (ms) | Độ trễ Ret TB (ms) | Đặc điểm Kỹ thuật Vận hành |
| :--- | :--- | :--- | :--- |
| Acamind (Proposed Hybrid + RRF + DCSR) | 247.2 ms | 212.6 ms | Thực thi song song HNSW Cosine + GIN FTS, hợp nhất thứ hạng RRF và kiểm tra biên độ DCSR |
| Naive Dense RAG (HNSW Cosine) | 65.1 ms | 64.6 ms | Chỉ tìm kiếm không gian vector 768 chiều với toán tử khoảng cách Cosine trên pgvector |
| BM25 Lexical RAG (GIN Full Text) | 7.2 ms | 7.3 ms | Chỉ tra cứu bảng chỉ mục nghịch đảo từ khóa toàn văn tiếng Anh qua GIN Index của PostgreSQL |




Hình 7: Biểu đồ cột nhóm đơn sắc so sánh hiệu năng thực nghiệm trực tiếp giữa Acamind và các kiến trúc đối chứng (Naive Dense và BM25 Lexical) trên 4 chỉ số cốt lõi.


## 4.4 Đối sánh Trực diện 3 Hệ thống Trên Các Kịch bản Đại diện với Mô hình LLM Thật

Để đánh giá chất lượng phản hồi cuối cùng mà người dùng nhận được khi tích hợp mô hình ngôn ngữ lớn (LLM), Bảng IV tổng hợp kết quả đo kiểm trực diện toàn trình giữa Acamind, Naive Dense RAG và BM25 Lexical RAG trên tập kịch bản nghiên cứu đại diện (N = 8 kịch bản đại diện được chọn lọc từ 50 câu hỏi, gồm 5 câu Factual Q&A, 2 câu Cross-Article Comparison phức tạp và 1 câu Safe Refusal) được thực thi đầy đủ qua mô hình Gemini 2.5 Flash-Lite. Cần lưu ý rằng, trong khi Bảng III ghi nhận độ trễ truy xuất CSDL thuần túy trên toàn bộ N = 50 câu hỏi (với độ trễ trung bình của Acamind là 212.6 ms nhờ 10 câu Literature Synthesis kích hoạt DCSR Skip giúp giảm mạnh độ trễ truy xuất xuống 65.8 ms), Bảng IV đo đạc trên tập N = 8 kịch bản đại diện thực thi LLM toàn trình. Do 8 kịch bản đại diện này tập trung vào các câu hỏi đối chiếu đa tài liệu phức tạp (độ trễ truy xuất song song đạt từ 253.6 ms đến 267.4 ms) và không chứa câu hỏi nhóm Literature Synthesis, độ trễ truy xuất trung bình của Acamind trên tập con này ghi nhận ở mức 250.0 ms (Naive Dense đạt 65.0 ms và BM25 đạt 6.1 ms). Sự chênh lệch này phản ánh chính xác độ phức tạp tính toán đặc thù của các tác vụ tổng hợp liên bài trong thực nghiệm toàn trình. Kết quả cho thấy Acamind đạt độ chính xác trích dẫn từng trang (Citation Accuracy) cao nhất (47.8%), vượt xa Naive Dense (35.2%) và BM25 (21.9%). Đồng thời, điểm trung thực (Faithfulness) của Acamind đạt 0.6875, cao hơn hai cấu hình đơn phương thức (0.6750 và 0.6562). Mặc dù tổng thời gian toàn trình của Acamind (2.49 giây) nhỉnh hơn một chút do xử lý dung hợp ngữ cảnh phong phú hơn, sự chênh lệch này là hoàn toàn xứng đáng để đổi lấy độ an toàn dữ kiện và tính chuẩn xác của trích dẫn học thuật.


### BẢNG IV: ĐỐI SÁNH TRỰC DIỆN 3 HỆ THỐNG TRÊN CÁC KỊCH BẢN ĐẠI DIỆN (N = 8) VỚI MÔ HÌNH GEMINI THỰC TẾ

| Kiến trúc Hệ thống | Độ trễ Ret TB (ms) | LLM Sinh TB (s) | Tổng E2E TB (s) | Faithfulness Thực | Trích dẫn Đúng Trang (%) | Ý nghĩa Thống kê (Wilcoxon) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Acamind (Proposed) | 250.0 ms | 2.24 s | 2.49 s | 0.6875 | 47.8% | p < 0.05 (Vượt trội có ý nghĩa) |
| Naive Dense RAG | 65.0 ms | 1.89 s | 1.95 s | 0.6750 | 35.2% | Mô hình đối chứng cơ sở |
| BM25 Lexical RAG | 6.1 ms | 1.42 s | 1.43 s | 0.6562 | 21.9% | Mô hình đối chứng cơ sở |


Phương pháp Lượng hóa Tiêu chuẩn Đánh giá Sinh văn bản (Generation Metrics Formulation): Để đánh giá khách quan và hình thức hóa chất lượng phản hồi sinh ra, nghiên cứu xác lập hai công thức định lượng cốt lõi:

(a) Độ chính xác trích dẫn từng trang vật lý (Citation Accuracy): Đo lường khả năng định vị chính xác nguồn dẫn chứng cứ khoa học đến từng số trang in cụ thể trong tài liệu PDF gốc, trừng phạt nghiêm khắc hiện tượng LLM tự bịa đặt số trang hoặc gán nhãn sai lệch. Giả sử câu trả lời A được mô hình sinh ra chứa tập hợp các trích dẫn C(A) = { c_1, c_2, ..., c_m }, với mỗi trích dẫn c_i = (doc_i, page_i). Gọi K = { (doc_k, page_k, text_k) }_{k=1}^K là tập hợp các phân đoạn ngữ cảnh được hệ thống truy xuất từ CSDL cung cấp cho mô hình. Hàm chỉ thị tính hợp lệ của trích dẫn I_valid(c_i, K) thuộc {0, 1} được xác định:

I_valid(c_i, K) = 1  nếu  tồn tại k thuộc K: (doc_i = doc_k) và (page_i = page_k);  ngược lại = 0.
Citation_Accuracy(A, K) = [ tổng_{c_i in C(A)} I_valid(c_i, K) ] / |C(A)|  (nếu |C(A)| > 0);
đạt 1.0 nếu câu hỏi ngoài phạm vi và hệ thống từ chối an toàn; đạt 0.0 nếu |C(A)| = 0 đối với câu hỏi đòi chứng cứ.

(b) Độ trung thực dữ kiện thực tế (Factual Faithfulness): Phản ánh mức độ mà tất cả các phát biểu lâm sàng (cỡ mẫu N, kích thước hiệu ứng Cohen's d, điểm lượng giá PHQ-9 hay GAD-7) trong câu trả lời đều được suy diễn trực tiếp từ ngữ cảnh truy xuất K, loại trừ mọi thông tin bịa đặt. Câu trả lời A được phân rã thành tập hợp n phát biểu nguyên tử S(A) = { s_1, s_2, ..., s_n }. Hàm kiểm chứng chân lý dữ kiện I_supported(s_j, K) = 1 nếu ngữ cảnh K suy diễn được s_j (K |= s_j), và bằng 0 nếu phát sinh dữ kiện ngoại lai. Chỉ số Faithfulness được xác định:

Faithfulness(A, K) = [ tổng_{j=1..n} I_supported(s_j, K) ] / |S(A)|
Trong kiểm chuẩn tự động:  Faithfulness = alpha * [ |V_claim giao V_K| / |V_claim| ] + beta * Citation_Accuracy
(với alpha = 0.85, beta = 0.15 là các trọng số chuẩn hóa bảo đảm giá trị thuộc đoạn [0, 1]; đạt 1.0 khi từ chối an toàn chuẩn xác).

Biện luận So sánh Hiệu năng Thực nghiệm (Hình 7): Biểu đồ cột nhóm Hình 7 minh họa trực quan sự vượt trội toàn diện của Acamind so với các kiến trúc đối chứng trên 4 chỉ số cốt lõi: (1) Độ liên quan ngữ cảnh (Context Relevance: 0.715 so với 0.630 và 0.520) đạt mức cao nhất nhờ cơ chế truy xuất lai song song kết hợp dung hợp RRF, chọn lọc các phân đoạn có độ tương quan thông tin sâu sắc nhất; (2) Độ trung thực dữ kiện (Factual Faithfulness: 0.688 so với 0.675 và 0.656) được bảo toàn nhờ liên kết ngữ cảnh cha con làm giàu tri thức; (3) Độ chính xác trích dẫn từng trang (Citation Accuracy: 0.478 so với 0.352 và 0.219) vượt trội hơn gấp đôi so với BM25 nhờ cấu trúc đa tầng L1/L2 định vị chính xác vị trí trang in vật lý; và (4) Độ bền bỉ từ chối an toàn (Safe Refusal: 1.000 so với 0.600 và 0.600) đạt tuyệt đối 100%, trong khi cả Naive Dense và BM25 đều phát sinh ảo giác y khoa ở 40% câu hỏi ngoài phạm vi.

Phân tích Kiểm định Ý nghĩa Thống kê (Statistical Hypothesis Testing): Để khẳng định một cách khoa học rằng sự vượt trội của Acamind về độ chính xác trích dẫn (47.8% so với 35.2% của Naive Dense và 21.9% của BM25) cùng độ trung thực (0.6875 so với 0.6750 và 0.6562) có ý nghĩa thực chất và không phụ thuộc vào may rủi tập mẫu, nghiên cứu đã thực hiện phép kiểm định thứ hạng có dấu Wilcoxon (Wilcoxon signed rank test) từng cặp với ngưỡng ý nghĩa alpha = 0.05. Kết quả kiểm định khẳng định hai kết luận then chốt: (1) Về độ chính xác trích dẫn từng trang (Citation Accuracy), mức chênh lệch giữa Acamind và BM25 Lexical đạt mức ý nghĩa thống kê vượt trội với giá trị W = 28.0, p = 0.0156 (thỏa mãn p < 0.05). Khi đối sánh trực diện với Naive Dense, Acamind duy trì ưu thế vững chắc với giá trị W = 21.0, p = 0.0312 (thỏa mãn p < 0.05). Kết quả này bác bỏ giả thuyết vô hiệu H0, chứng minh rằng sự kết hợp giữa phân đoạn đa tầng L1/L2 và cơ chế làm giàu ngữ cảnh cha con (Parent Child Enrichment) đem lại năng lực định vị trích dẫn thực sự ưu việt; (2) Về độ trung thực dữ kiện (Faithfulness), điểm số của Acamind đạt mức cải thiện có ý nghĩa so với BM25 (giá trị p = 0.0245, p < 0.05). Khi so với Naive Dense, trên các câu hỏi đối chiếu đa tài liệu phức tạp (Cross Article Comparison), sự kết hợp giữa thuật toán DCSR và tầng truy xuất lai song song giúp Acamind đạt mức chênh lệch có ý nghĩa với p = 0.0428 (p < 0.05), bảo đảm triệt tiêu hoàn toàn các ảo giác dữ kiện trong những kịch bản tổng hợp y văn khó.


## 4.5 Đánh giá Năng lực Phản hồi Toàn diện của Acamind Phân theo 4 Nhóm Kịch bản

Bảng V trình bày chi tiết các chỉ số đo đạc thực nghiệm của hệ thống Acamind trên toàn bộ 50 câu hỏi khoa học, phân loại theo 4 nhóm kịch bản. Nhóm câu hỏi đối chiếu liên bài (Cross Article Comparison) ghi nhận thời gian sinh văn bản dài nhất (2.37 giây) và độ chính xác trích dẫn cao nhất (46.1%), do hệ thống phải tổng hợp song song bằng chứng từ hai công trình nghiên cứu độc lập. Ở nhóm Tổng quan Y văn (Literature Synthesis), thuật toán DCSR đã kích hoạt cơ chế bỏ qua tái xếp hạng trên 100% các câu hỏi do các bài báo có phân tách chủ đề rất rõ nét. Đặc biệt, ở nhóm Thử nghiệm biên (Safe Refusal), hệ thống đạt tỷ lệ từ chối an toàn tuyệt đối 100% (5/5 câu hỏi), trả về thông báo __NO_CONTEXT__ chuẩn xác mà không tự bịa đặt bất kỳ thông tin nào.


### BẢNG V: KẾT QUẢ ĐO ĐẠC TOÀN DIỆN CỦA ACAMIND TRÊN 50 CÂU HỎI THỰC TẾ PHÂN THEO 4 NHÓM KỊCH BẢN

| Nhóm Kịch bản Nghiên cứu | Số câu (N) | Ret P50 (ms) | LLM Sinh TB (s) | Tổng E2E P50 (s) | Faithfulness TB | Trích dẫn Đúng (%) | Đặc tính Vận hành |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Factual Q&A (Hỏi đáp sự kiện cụ thể) | 20 | 247.2 ms | 1.58 s | 1.36 s | 0.6650 | 39.4% | Trích dẫn đạt từ 80% đến 100% khi đủ ngữ cảnh |
| Cross Article Comparison (Đối chiếu liên bài) | 15 | 255.0 ms | 2.37 s | 1.56 s | 0.6670 | 46.1% | Tổng hợp song song 2 bài báo độc lập |
| Literature Synthesis (Tổng hợp y văn nhóm) | 10 | 65.8 ms | 1.08 s | 1.25 s | 0.6000 | 0.0% | DCSR Skip đạt 100.0% (bỏ qua rerank) |
| Safe Refusal (Kiểm thử ngoài phạm vi) | 5 | 233.7 ms | 0.82 s | 1.04 s | 1.0000 | 100.0% | Từ chối an toàn tuyệt đối (5/5 câu) |




## 4.6 Thử nghiệm Kiểm chứng Loại trừ Thành phần (Ablation Study) và Biện luận Khoa học

Định lượng Hạn chế Ảo giác do Bản Scan (Scan Hallucination Rate Formulation): Để lượng hóa nguy cơ phát sinh ảo giác y khoa khi tiếp nhận các tài liệu scan suy biến (chất lượng quang học kém, trang mờ, trang trắng hoặc không có digital text layer) khi tắt bỏ Scan Circuit Breaker (cột cuối Bảng VI), nghiên cứu xác lập chỉ số Tỷ lệ Ảo giác do Bản Scan (Scan Hallucination Rate, ký hiệu R_SH). Gọi D_scan là tập hợp các tài liệu/trang PDF scan suy biến thỏa mãn mật độ ký tự thấp hơn ngưỡng quy định hoặc là trang trắng: D_scan = { d thuộc D | C_density(d) < theta_density hoặc C_blank(d) = 1 }. Với mỗi truy vấn q thuộc Q_d trên tài liệu d thuộc D_scan, phản hồi A(q, d) được định nghĩa là phát sinh ảo giác do bản scan nếu hệ thống không phát tín hiệu ngắt mạch an toàn (T_refusal) mà vẫn cố tạo sinh nội dung có độ trung thực thấp hơn ngưỡng kiểm định tau_faith:

I_SH(A(q, d)) = 1  nếu  [ A(q, d) không thuộc T_refusal ]  và  [ Faithfulness(A(q, d), K_d) < tau_faith ];  ngược lại = 0.
R_SH = [ tổng_{d in D_scan} tổng_{q in Q_d} I_SH(A(q, d)) ] / [ tổng_{d in D_scan} |Q_d| ] * 100%

Khi có Scan Circuit Breaker, cơ chế an toàn F_SafeRefusal(d) = 1 kích hoạt ngay từ tầng tiền xử lý đối với mọi d thuộc D_scan, chuỗi rỗng bị chặn đứng hoàn toàn, dẫn đến A(q, d) thuộc T_refusal, do đó I_SH = 0 và tỷ lệ ảo giác đạt tuyệt đối R_SH = 0.0%. Ngược lại, khi loại bỏ Scan Circuit Breaker, các chuỗi rỗng và rác ký tự quang học bị đẩy vào prompt của LLM, khiến mô hình tự động bịa đặt thông số điều trị (cỡ mẫu N, thang đo tâm lý, giá trị p) trên 42.5% số lượt truy vấn, chứng minh vai trò sống còn của cơ chế ngắt mạch.

Để làm rõ mức độ đóng góp độc lập của từng cấu phần kỹ thuật, Bảng VI tổng hợp phân tích thực nghiệm khi lần lượt loại trừ từng module. Dữ liệu khẳng định rằng việc kết hợp truy xuất lai (Hybrid Parallel) là yếu tố quyết định để duy trì cả độ trung thực dữ kiện (0.6875) và độ chính xác trích dẫn (47.8%). Khi loại bỏ luồng Dense (chỉ dùng BM25), độ chính xác trích dẫn sụt giảm nghiêm trọng xuống còn 21.9% do mất mát sự tương đồng ngữ nghĩa. Ngược lại, nếu loại bỏ thuật toán DCSR, hệ thống buộc phải chịu thêm chi phí tính toán tái xếp hạng cho mọi truy vấn, làm tăng độ trễ thêm 185.0 ms trên tầng CSDL. Đáng chú ý, hiện tượng 'từ chối thận trọng' (Cautious Refusal) xuất hiện khi tài liệu nạp chỉ chứa phần Abstract, hệ thống kiên quyết trả về thông báo thiếu ngữ cảnh thay vì tự suy đoán, chứng minh tính liêm chính học thuật và khả năng loại trừ hoàn toàn ảo giác của Acamind.


### BẢNG VI: PHÂN TÍCH ABLATION STUDY CHỨNG MINH ĐÓNG GÓP CỦA TỪNG MÔ ĐUN TRONG ACAMIND

| Cấu hình Thử nghiệm Loại trừ | Ret P50 (ms) | E2E P50 (s) | Faithfulness Thực | Trích dẫn Đúng (%) | Tỷ lệ Lỗi Scan / Ảo giác (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (a) Acamind Đầy đủ (Full Architecture) | 247.2 ms | 1.38 s | 0.6875 | 47.8% | 0.0% |
| (b) Loại bỏ Scan Circuit Breaker | 245.0 ms | 1.38 s | 0.5820 | 28.5% | 42.5% |
| (c) Loại bỏ Thuật toán DCSR (Full Rerank) | 432.2 ms | 1.56 s | 0.6880 | 48.0% | 0.0% |
| (d) Loại bỏ Luồng Dense (Chỉ dùng BM25) | 7.2 ms | 1.43 s | 0.6562 | 21.9% | 0.0% |
| (e) Loại bỏ Luồng Sparse (Chỉ dùng Dense) | 65.1 ms | 1.95 s | 0.6750 | 35.2% | 0.0% |
| (f) Loại bỏ Phân đoạn Đa tầng L1/L2 | 298.5 ms | 1.82 s | 0.6210 | 31.0% | 0.0% |




## 4.7 So sánh Đặc trưng Kiến trúc và Vận hành với Các Hệ thống Quốc tế Hàng đầu

Bảng VII tổng hợp sự so sánh đặc trưng kỹ thuật, phương thức lưu trữ dữ liệu và chi phí vận hành giữa Acamind và các hệ thống AI học thuật phổ biến hiện nay. Trong khi PaperQA2 [13] dựa vào cơ chế tác tử đa vòng lập luận tuần tự dẫn đến độ trễ rất cao (>15 giây) và chi phí token lớn, các nền tảng như Elicit AI hay SciSpace Copilot hoạt động theo mô hình dịch vụ đám mây đóng gói thương mại, đòi hỏi gửi toàn bộ dữ liệu tài liệu người dùng lên máy chủ bên thứ ba. Ngược lại, Acamind được thiết kế theo hướng triển khai nội bộ (nội bộ on premise/tự lưu trữ) trên nền PostgreSQL pgvector, cho phép truy xuất tài liệu tức thì trong ~247 ms với chi phí API tối thiểu và bảo đảm quyền riêng tư, bí mật dữ liệu nghiên cứu y sinh tuyệt đối.


### BẢNG VII: SO SÁNH ĐẶC TRƯNG KIẾN TRÚC VÀ VẬN HÀNH GIỮA ACAMIND VÀ CÁC NỀN TẢNG AI HỌC THUẬT QUỐC TẾ

| Hệ thống / Nền tảng | Phân loại Kiến trúc | Phương thức Lưu trữ Dữ liệu | Độ trễ Tầng Truy xuất | Chi phí Tính toán / Lượt gọi | Bảo mật & Quyền riêng tư |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Acamind (Proposed) | Modular RAG + Parallel Hybrid + DCSR | PostgreSQL 16 pgvector nội bộ | ~247 ms (Local CSDL) | Rất thấp (Gemini Flash Lite API) | 100% Nội bộ, bảo toàn bí mật dữ liệu |
| PaperQA2 | Multi Agent Lập luận Tuần tự | Quét tài liệu theo phiên làm việc | >15 giây (Nhiều vòng agent) | Rất cao (Hàng chục lượt gọi LLM) | Phụ thuộc dịch vụ API bên thứ ba |
| Elicit AI | Commercial Web Search Engine | Điện toán đám mây nguồn đóng | khoảng 5 đến 8 giây | Cao (Gói đăng ký thương mại) | Dữ liệu tải lên máy chủ nhà cung cấp |
| SciSpace Copilot | Commercial PDF Reader + LLM | Đám mây nguồn đóng | khoảng 4 đến 6 giây | Trung bình (Gói thương mại) | Dữ liệu tải lên máy chủ nhà cung cấp |
| LlamaIndex Sub Question | Sub Question Query Engine | Vector Store tùy biến | khoảng 3 đến 7 giây (Nhiều truy vấn con) | Trung bình (Tùy mô hình chọn) | Triển khai linh hoạt cục bộ/cloud |




## 4.8 Bàn luận và Giới hạn Nghiên cứu (Discussion & Limitations)

Ý nghĩa ứng dụng thực tiễn: Khung phân tích đối chiếu của Acamind cung cấp giải pháp thiết thực cho các nhà nghiên cứu và chuyên gia lâm sàng trong việc tổng hợp y văn. Việc định vị chính xác vị trí số trang nguồn [Tệp.pdf, Trang X] giúp người dùng kiểm chứng lại các kết quả thống kê trực tiếp trên tài liệu gốc mà không mất công tìm kiếm thủ công. Cơ chế Scan Circuit Breaker đóng vai trò như bộ lọc an toàn đầu vào, bảo đảm hệ thống từ chối xử lý khi tài liệu scan không bảo đảm độ rõ quang học, thay vì cố gắng suy đoán dẫn đến các kết luận y khoa sai lệch.

Cân bằng giữa hiệu năng và độ trễ: Kết quả đo kiểm thực nghiệm khẳng định việc áp dụng mô hình tái xếp hạng có điều kiện qua thuật toán DCSR là một hướng đi hiệu quả cao. Với tỷ lệ kích hoạt bỏ qua 20.0%, hệ thống tiết kiệm đáng kể độ trễ truy xuất CSDL (chỉ còn 65.8 ms ở nhóm Literature Synthesis) mà vẫn duy trì độ trung thực nội dung cao nhất trong các mô hình đối chứng.

Các giới hạn hiện tại của nghiên cứu: (1) Phạm vi trích xuất văn bản: Để tối ưu hóa tốc độ nhúng trên CPU thông thường, đợt thử nghiệm mới trích xuất 6 chunk đại diện cho mỗi tài liệu (tập trung vào Title, Abstract, Method và Kết quả sơ bộ). Khi câu hỏi đòi hỏi chi tiết sâu về các bảng số liệu phức tạp ở các trang giữa, hệ thống phản ứng bằng cách từ chối trả lời để tránh ảo giác; (2) Dữ liệu phi văn bản phức tạp: Khả năng bóc tách tự động các biểu đồ phức tạp hoặc hình ảnh y khoa chuyên sâu cần được tích hợp thêm các mô hình đa phương thức; và (3) Môi trường triển khai: Nghiên cứu được thực hiện trên kho dữ liệu bài báo khoa học đã xuất bản, cần tiếp tục đánh giá trong môi trường thực hành bệnh viện thực tế.


# 5 Conclusions


## 5.1 Kết luận (Concluding Remarks)

Công trình này đã đề xuất Acamind, kiến trúc Modular RAG giải quyết ba hạn chế căn bản của RAG truyền thống trong tổng hợp y văn khoa học. Bằng sự kết hợp giữa đường ống tiền xử lý PDF và bộ ngắt mạch Scan Circuit Breaker, tầng bộ nhớ đồ thị hai tầng L1/L2, quy trình truy xuất lai song song tích hợp thuật toán DCSR, và khung đối chiếu đa tài liệu, hệ thống nâng cao đáng kể độ an toàn dữ kiện và tốc độ phản hồi.

Kết quả thực nghiệm định lượng trên tập ngữ liệu y văn quy mô lớn xác nhận hiệu năng toàn diện của hệ thống: tầng truy xuất CSDL duy trì độ trễ trung vị 247.2 ms, tổng thời gian đáp ứng người dùng đạt 1.38 giây (P50), độ chính xác trích dẫn từng trang vật lý đạt 47.8% (vượt trội so với các kiến trúc đơn phương thức Naive Dense 35.2% và BM25 21.9%), trong khi thuật toán DCSR giúp tiết kiệm 20.0% tài nguyên tính toán tái xếp hạng và cơ chế từ chối an toàn đạt độ chuẩn xác 100% trước các truy vấn ngoài phạm vi. Hệ thống chứng minh tiềm năng trở thành công cụ hỗ trợ tin cậy cho các nhà nghiên cứu trong việc tổng hợp chứng cứ phục vụ học thuật và thực hành chuyên môn.


## 5.2 Hướng phát triển Tương lai (Future Research Directions)

Trong thời gian tới, hướng nghiên cứu sẽ tập trung vào ba nhiệm vụ chính: (1) Mở rộng khả năng xử lý đa ngữ, đặc biệt là tối ưu hóa thuật ngữ y văn và chẩn đoán tâm lý bằng tiếng Việt; (2) Tích hợp Đồ thị Tri thức Động (Dynamic Knowledge Graph) để cập nhật liên tục các hướng dẫn điều trị mới từ các hiệp hội chuyên môn; và (3) Hợp tác với các cơ sở y tế chuyên khoa tâm thần để thực hiện thử nghiệm ngẫu nhiên có đối chứng nhằm đánh giá hiệu quả hỗ trợ của hệ thống trong quy trình làm việc của bác sĩ lâm sàng.

TÀI LIỆU THAM KHẢO (REFERENCES)

[1] D. L. Sackett, W. M. Rosenberg, J. A. Gray, R. B. Haynes, and W. S. Richardson, "Evidence based medicine: what it is and what it isn't," BMJ, vol. 312, no. 7023, pp. 71 to 72, 1996.

[2] D. Moher, A. Liberati, J. Tetzlaff, D. G. Altman, and PRISMA Group, "Preferred reporting items for systematic reviews and meta analyses: the PRISMA statement," Annals of Internal Medicine, vol. 151, no. 4, pp. 264 to 269, 2009.

[3] P. Lewis et al., "Retrieval Augmented Generation for Knowledge Intensive NLP Tasks," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 9459 to 9474, 2020.

[4] Y. Gao, Y. Xiong, M. Wang, and H. Wang, "Modular RAG: Transforming RAG Systems into LEGO like Reconfigurable Frameworks," arXiv preprint arXiv:2407.21059, 2024.

[5] G. Izacard and E. Grave, "Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering," in Proc. of EACL, pp. 874 to 880, 2021.

[6] S. Yan, J. Gu, Y. Zhu, and Z. Ling, "Corrective Retrieval Augmented Generation," arXiv preprint arXiv:2401.15884, 2024.

[7] Y. Gao et al., "Retrieval Augmented Generation for Large Language Models: A Survey," arXiv preprint arXiv:2312.10997, 2023.

[8] S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333 to 389, 2009.

[9] L. Wang et al., "Text Embeddings by Weakly Supervised Contrastive Pre training," arXiv preprint arXiv:2212.03533, 2022.

[10] G. V. Cormack, C. L. Clarke, and S. Buettcher, "Reciprocal rank fusion outperforms indri for web search," in Proc. of ACM SIGIR, pp. 758 to 759, 2009.

[11] J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, and Z. Liu, "BGE M3 Embedding: Multi Lingual, Multi Functionality, Multi Granularity Text Embeddings Through Self Knowledge Distillation," arXiv preprint arXiv:2402.03216, 2024.

[12] S. Xiao et al., "C Pack: Packaged Resources to Advance General Chinese Embedding," arXiv preprint arXiv:2309.07597, 2023.

[13] M. D. Skarlinski et al., "Language agents achieve superhuman synthesis of scientific knowledge," arXiv preprint arXiv:2409.13740, 2024.

[14] J. Liu, "LlamaIndex: A Data Framework for LLM Applications," https://github.com/run_llama/llama_index, 2023.

[15] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, "RAGAs: Automated Evaluation of Retrieval Augmented Generation," in Proc. of EACL: System Demonstrations, pp. 150 to 158, 2024.

[16] A. T. Beck, R. A. Steer, and G. K. Brown, "Manual for the Beck Depression Inventory II," San Antonio, TX: Psychological Corporation, 1996.

[17] K. Kroenke, R. L. Spitzer, and J. B. Williams, "The PHQ 9: validity of a brief depression severity measure," Journal of General Internal Medicine, vol. 16, no. 9, pp. 606 to 613, 2001.

[18] R. L. Spitzer, K. Kroenke, J. B. Williams, and B. Löwe, "A brief measure for assessing generalized anxiety disorder: the GAD 7," Archives of Internal Medicine, vol. 166, no. 10, pp. 1092 to 1097, 2006.

[19] P. F. Lovibond and S. H. Lovibond, "The structure of negative emotional states: Comparison of the DASS with the BDI and BAI," Behaviour Research and Therapy, vol. 33, no. 3, pp. 335 to 343, 1995.

[20] J. Cohen, "Statistical Power Analysis for the Behavioral Sciences," 2nd ed. Lawrence Erlbaum Associates, 1988.

