import csv
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Desktop\Acamind\Query and result")
source = ROOT / "300_cau_hoi_tam_ly_hoc.csv"
draft = ROOT / "answer_drafts_checkpoint.json"
output = ROOT / "300_cau_tra_loi_tam_ly_hoc_tham_khao.csv"
rows = list(csv.DictReader(source.open(encoding="utf-8-sig", newline="")))
answers = json.loads(draft.read_text(encoding="utf-8"))

BASE = "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf"
APA = "https://www.apa.org/topics"
SOURCES = [
    (r"tâm động học", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10168167/"),
    (r"cặp đôi|Gottman|\bEFT\b", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13474905/"),
    (r"nghiện chất|mười hai bước|cai nghiện|liệu pháp nhóm", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8215831/"),
    (r"4-7-8|hít thở|thở chậm", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8302658/"),
    (r"phản hồi sinh học|biofeedback", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12763951/"),
    (r"theo dõi tiến triển|kết thúc trị liệu|kế hoạch điều trị", "https://pmc.ncbi.nlm.nih.gov/articles/PMC11076375/"),
    (r"PHQ-9|GAD-7", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5681977/"),
    (r"ánh sáng|theo mùa", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3181778/"),
    (r"Rorschach", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9225754/"),
    (r"dừng suy nghĩ", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3307846/"),
    (r"thực tế ảo", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13033945/"),
    (r"âm nhạc", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6486188/"),
    (r"nghệ thuật", "https://pmc.ncbi.nlm.nih.gov/articles/PMC11725198/"),
    (r"thôi miên", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10807512/"),
    (r"benzodiazepine|thuốc an thần", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12463801/"),
    (r"sốc điện|\bECT\b", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10096214/"),
    (r"mất ngủ|giấc ngủ|CBT-I", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7853203/"),
    (r"tự tử|tự hại|kế hoạch an toàn", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10172548/"),
    (r"sang chấn|PTSD|EMDR|tiếp xúc kéo dài", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8471692/"),
    (r"ADHD|tăng động giảm chú ý|thuốc kích thích", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10363932/"),
    (r"tự kỷ", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6345133/"),
    (r"OCD|ám ảnh cưỡng chế|ngăn ngừa phản ứng", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12900050/"),
    (r"lưỡng cực|lithium|ổn định khí sắc", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12900052/"),
    (r"tâm thần phân liệt|loạn thần|chống loạn thần", "https://pmc.ncbi.nlm.nih.gov/articles/PMC13000005/"),
    (r"nhân cách ranh giới|\bDBT\b|hành vi biện chứng", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10096204/"),
    (r"lo âu|hoảng sợ|ám ảnh sợ|tiếp xúc|\bCBT\b", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7001348/"),
    (r"trầm cảm|chống trầm cảm|\bSSRI\b|\bPHQ-9\b", "https://pmc.ncbi.nlm.nih.gov/articles/PMC11351064/"),
    (r"ăn uống|chán ăn|ăn vô độ", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10864000/"),
    (r"\bACT\b|chánh niệm|\bMBSR\b", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10523914/"),
    (r"nhân cách|big five|ngoại hướng|nội hướng", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10142293/"),
    (r"trí nhớ|học tập|trí tuệ|Piaget|Freud|Jung|Adler|phân tâm|Maslow|Bandura|Skinner", BASE),
]

FIXES = {
    "Q020": "Rối loạn nhân cách ranh giới là kiểu mẫu dai dẳng của bất ổn cảm xúc, hình ảnh bản thân và quan hệ, thường kèm sợ bị bỏ rơi, bốc đồng hoặc hành vi tự hại. Khi đánh giá, hỏi trực tiếp về ý nghĩ tự sát, kế hoạch, phương tiện, tiền sử hành vi và yếu tố bảo vệ; thang sàng lọc không thay thế phỏng vấn lâm sàng. Kế hoạch an toàn cần nhận diện dấu hiệu cảnh báo, cách ứng phó, người hỗ trợ, đầu mối cấp cứu và giảm tiếp cận phương tiện gây hại; không dựa vào 'cam kết không tự tử'.",
    "Q028": "Tâm thần phân liệt là rối loạn loạn thần kéo dài có thể ảnh hưởng nhận thức, cảm xúc, hành vi và chức năng. Triệu chứng dương tính gồm hoang tưởng, ảo giác, lời nói hoặc hành vi vô tổ chức; triệu chứng âm tính gồm giảm biểu lộ cảm xúc, giảm động lực và lời nói. Đánh giá phân biệt với loạn thần do chất hoặc bệnh cơ thể, rối loạn khí sắc có loạn thần và rối loạn phân liệt cảm xúc, dựa trên diễn tiến thời gian và khám lâm sàng theo tiêu chuẩn chẩn đoán hiện hành.",
    "Q021": "Thuyết Piaget gồm bốn giai đoạn: cảm giác–vận động (khoảng 0–2 tuổi), tiền thao tác (2–7 tuổi), thao tác cụ thể (7–11 tuổi) và thao tác hình thức (từ khoảng 12 tuổi). Mốc tuổi chỉ mang tính gần đúng; phát triển có khác biệt giữa các cá nhân.",
    "Q114": "ADHD nổi bật ở tình trạng thiếu chú ý và/hoặc tăng động, bốc đồng; tự kỷ nổi bật ở khác biệt dai dẳng trong giao tiếp xã hội cùng hành vi hoặc sở thích hạn chế, lặp lại. Khó khăn xã hội có thể xuất hiện ở cả hai và hai tình trạng có thể đồng mắc, nên cần đánh giá phát triển toàn diện thay vì suy diễn từ một biểu hiện. Can thiệp ADHD thường gồm hỗ trợ hành vi, môi trường học tập và khi phù hợp là thuốc; can thiệp tự kỷ chú trọng hỗ trợ giao tiếp, thích nghi và nhu cầu cá nhân, với gia đình tham gia.",
    "Q130": "Cách chia 'mất ngủ nguyên phát' và 'thứ phát' hiện có giới hạn vì mất ngủ và trầm cảm có thể tác động hai chiều. Cần đánh giá thời điểm khởi phát, kiểu mất ngủ, triệu chứng khí sắc, thuốc và bệnh lý kèm theo. CBT-I là điều trị hàng đầu cho mất ngủ mạn tính, kể cả khi có bệnh đồng mắc; đồng thời điều trị trầm cảm nếu hiện diện, thay vì chờ xử lý trầm cảm rồi mới chữa mất ngủ.",
    "Q112": "Freud nhấn mạnh xung đột vô thức, các xung năng và trải nghiệm sớm; Adler đặt trọng tâm vào cảm giác tự ti, sự bù trừ, mục tiêu sống và mối quan tâm xã hội. Mặc cảm tự ti là khái niệm trung tâm của Adler, không phải của Freud. Cả hai là các lý thuyết lịch sử cần phân biệt với những kết luận thực nghiệm hiện đại.",
    "Q127": "Trí tuệ linh hoạt là năng lực suy luận và giải quyết vấn đề mới với ít phụ thuộc vào kiến thức tích lũy. Trí tuệ kết tinh là kiến thức, từ vựng và kỹ năng học được qua giáo dục, kinh nghiệm. Trung bình, một số năng lực linh hoạt suy giảm sớm hơn theo tuổi, còn năng lực kết tinh thường được duy trì lâu hơn; thời điểm và mức độ thay đổi khác nhau giữa người và phép đo.",
    "Q129": "Lòng tự trọng cao là đánh giá tích cực về giá trị bản thân và có thể đi cùng sự tự chấp nhận. Tính tự ái chỉ một nhóm đặc điểm như cảm giác mình đặc biệt, nhu cầu được ngưỡng mộ và khó đồng cảm ở mức độ khác nhau; tự ái bệnh lý cần đánh giá mẫu hình kéo dài và suy giảm chức năng. Không thể suy ra rằng mọi người có tính tự ái đều bí mật thiếu tự tin hoặc rằng người tự trọng cao không bao giờ nhạy cảm với phê bình.",
    "Q141": "Tic là cử động hoặc âm thanh đột ngột, nhanh, lặp lại và thường có cảm giác thôi thúc trước khi xảy ra. Hành vi lặp lại trong tự kỷ có thể gồm chuyển động rập khuôn, lời nói lặp lại hoặc thói quen cứng nhắc; chúng thường khác tic về nhịp điệu, thời lượng và bối cảnh. Hai hiện tượng có thể đồng mắc, nên đánh giá chức năng và diễn tiến thay vì cho rằng hành vi tự kỷ luôn có chủ ý.",
    "Q149": "Trầm cảm quanh sinh có các triệu chứng trầm cảm xuất hiện trong thai kỳ hoặc sau sinh; triệu chứng cốt lõi giống trầm cảm ở thời điểm khác nhưng diễn ra trong bối cảnh thay đổi sinh học, giấc ngủ và chăm sóc trẻ. Cần đánh giá mức độ suy giảm chức năng, ý nghĩ tự hại, triệu chứng loạn thần và tác động tới việc chăm sóc trẻ. Không phải mọi người mắc trầm cảm sau sinh đều có ý nghĩ làm hại trẻ; nếu có, cần hỏi rõ tính chất ý nghĩ và nguy cơ để can thiệp phù hợp.",
    "Q065": "Thuật ngữ 'rối loạn dạng cơ thể' thuộc cách phân loại cũ. Trong DSM-5, rối loạn triệu chứng cơ thể được nhận diện bởi một hay nhiều triệu chứng cơ thể gây đau khổ hoặc ảnh hưởng chức năng, kèm suy nghĩ, cảm xúc hoặc hành vi quá mức liên quan; triệu chứng không bắt buộc phải không có giải thích y khoa. Chẩn đoán cần đánh giá lâm sàng và loại trừ các tình trạng phù hợp.",
    "Q077": "Rorschach là trắc nghiệm vết mực được dùng để quan sát cách cá nhân tri giác và diễn giải kích thích mơ hồ, đôi khi bổ trợ đánh giá nhân cách hoặc tư duy. Giá trị của từng chỉ số còn gây tranh luận; không nên dùng riêng trắc nghiệm này để chẩn đoán hay suy ra 'khuyết tật tiềm ẩn'.",
    "Q198": "PHQ-9 gồm 9 mục đánh giá triệu chứng trầm cảm trong hai tuần; GAD-7 gồm 7 mục đánh giá triệu chứng lo âu trong hai tuần. Mỗi mục chấm 0–3; tổng điểm lần lượt 0–27 và 0–21. Ngưỡng 10 thường dùng để gợi ý đánh giá thêm, nhưng ngưỡng tối ưu thay đổi theo dân số và mục tiêu sàng lọc. Kết quả dương tính, đặc biệt mục 9 của PHQ-9 về ý nghĩ tự hại, cần được đánh giá lâm sàng và nguy cơ kịp thời; thang đo không tự xác lập chẩn đoán.",
    "Q220": "Thôi miên trị liệu thường gồm chuẩn bị và đồng thuận, hướng dẫn tập trung chú ý hoặc thư giãn, gợi ý trị liệu phù hợp mục tiêu, rồi định hướng trở lại và đánh giá trải nghiệm. Với ám ảnh sợ, bằng chứng cho thôi miên yếu hơn liệu pháp tiếp xúc dựa trên CBT, nên không nên trình bày như điều trị đầu tay. Cần thận trọng và đánh giá chuyên khoa khi có loạn thần, phân ly nặng hoặc nguy cơ mất ổn định; không coi mọi trường hợp đó là chống chỉ định tuyệt đối chung cho mọi kỹ thuật.",
    "Q249": "'Dừng suy nghĩ' là kỹ thuật cố ý ngắt một suy nghĩ gây khó chịu bằng tín hiệu như lời nhắc 'dừng', rồi chuyển sang hoạt động hoặc cách đối phó khác. Hiệu quả của việc cố gắng đè nén ý nghĩ xâm nhập không ổn định và đôi khi làm tăng sự chú ý vào ý nghĩ đó. Với OCD, tiếp xúc và ngăn ngừa phản ứng là phương pháp có bằng chứng tốt hơn; không dùng dừng suy nghĩ để thay thế ERP.",
    "Q255": "Thở 4-7-8 là nhịp hít vào khoảng 4 giây, giữ hơi khoảng 7 giây và thở ra khoảng 8 giây, thực hiện nhẹ nhàng vài chu kỳ nếu thấy dễ chịu. Nhịp thở chậm có thể giúp một số người ổn định cảm giác căng thẳng, nhưng bằng chứng riêng cho công thức 4-7-8 và hiệu quả cắt cơn lo âu còn hạn chế. Nếu giữ hơi gây chóng mặt hoặc khó chịu, nên dừng và thở tự nhiên.",
    "Q283": "ECT được cân nhắc cho trầm cảm nặng, đặc biệt khi có loạn thần, nguy cơ tự tử cao, từ chối ăn uống, kháng trị hoặc cần đáp ứng nhanh; cũng có chỉ định ở một số trường hợp hưng cảm và căng trương lực. Quyết định phải qua đánh giá chuyên khoa, cân nhắc lợi ích và tác dụng phụ cùng sự đồng thuận phù hợp.",
}
answers.update(FIXES)

def sources_for(question):
    urls = []
    for pattern, url in SOURCES:
        if re.search(pattern, question, flags=re.I) and url not in urls:
            urls.append(url)
        if len(urls) == 2:
            break
    return urls or [BASE, APA]

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]) + ["Cau_tra_loi_tham_khao", "Nguon_tham_khao", "Trang_thai_tham_dinh"])
    writer.writeheader()
    for row in rows:
        qid = row["Question_ID"]
        row["Cau_tra_loi_tham_khao"] = answers.get(qid, "")
        row["Nguon_tham_khao"] = "; ".join(sources_for(row["Câu hỏi"]))
        row["Trang_thai_tham_dinh"] = "Cần chuyên gia lâm sàng rà soát" if row["Câu hỏi"].lower().find("thuốc") >= 0 or any(x in row["Câu hỏi"].lower() for x in ("chẩn đoán", "điều trị", "tự tử", "tự hại")) else "Nguồn tham khảo theo chủ đề; chưa thẩm định từng mệnh đề"
        writer.writerow(row)
print(output)
print("rows", len(rows), "answered", sum(bool(answers.get(x["Question_ID"])) for x in rows))
