# Telco Association Rule Mining (Apriori)

Khai phá luật kết hợp bằng Apriori trên IBM Telco Customer Churn để trả lời 6 câu hỏi về đồng sử dụng dịch vụ, rời mạng, ở lại, phân nhóm nhân khẩu học và gợi ý bổ sung dịch vụ.

Kết quả đã chạy: [báo cáo trả lời 6 câu hỏi](outputs/answers_6_questions.md).

## Cấu trúc

```
KPDL/
├── data/raw/telco_customer_churn.csv
├── src/telco_arm/
│   ├── config.py          tham số, đường dẫn, đặc tả thuộc tính
│   ├── data_loader.py     đọc & làm sạch
│   ├── preprocessing.py   rời rạc hoá, tạo giao dịch, one-hot
│   ├── apriori.py         thuật toán Apriori (tự cài đặt)
│   ├── rules.py           sinh luật, Apriori có mục tiêu, tỉa luật dư thừa
│   ├── analysis.py        bảng tổng hợp, độ phủ, lift, độ nhạy ngưỡng
│   ├── questions.py       tính kết quả 6 câu hỏi và gợi ý theo khách hàng
│   ├── reporting.py       báo cáo tiếng Việt và metadata tái lập
│   ├── visualization.py   biểu đồ
│   └── pipeline.py        luồng xử lý end-to-end & xuất kết quả
├── notebooks/telco_apriori_analysis.ipynb
├── outputs/{tables,figures}/
├── tests/test_analysis.py
└── main.py
```

## Chạy

```bash
pip install -r requirements.txt
python main.py
python main.py --min-support 0.08 --min-confidence 0.75 --churn-support 0.02
python main.py --demographic-confidence 0.25 --min-group-customers 200 --recommendations-per-customer 2
python main.py --no-figures --top 5
jupyter notebook notebooks/telco_apriori_analysis.ipynb
```

`--data` chọn CSV đầu vào, `--output` chọn thư mục kết quả. `--top` chỉ giới hạn số dòng trong báo cáo và terminal; CSV giữ toàn bộ kết quả. Chạy trên Windows hỗ trợ xuất tiếng Việt UTF-8.

## Kết quả

| File | Nội dung |
|---|---|
| `answers_6_questions.md` | Báo cáo tiếng Việt, số liệu và diễn giải cho từng câu |
| `run_metadata.json` | Tham số, SHA-256 dữ liệu, số dòng làm sạch, ngưỡng phân vị |
| `tables/q1_service_bundles.csv` | Tổ hợp dịch vụ, số khách và support |
| `tables/q2_service_probabilities.csv` | P(B\|A), P(B), lift và mẫu số của mọi cặp dịch vụ |
| `tables/q3_churn_patterns.csv` | Luật rời mạng kèm số khách khớp và đúng nhãn |
| `tables/q4_retention_patterns.csv` | Luật ở lại kèm số khách khớp và đúng nhãn |
| `tables/q5_demographic_bundles.csv` | Nhóm nhân khẩu học → tổ hợp dịch vụ, tỷ lệ trong nhóm và lift |
| `tables/q6_upgrade_rules.csv` | Luật gợi ý và số khách đủ điều kiện |
| `tables/q6_customer_recommendations.csv` | Gợi ý theo từng khách, thứ hạng và luật làm căn cứ |
| `tables/frequent_itemsets.csv` | Tập phổ biến (hành vi dịch vụ) |
| `tables/service_rules.csv` | Luật đồng sử dụng dịch vụ |
| `tables/churn_rules.csv` | Luật `→ Churn=Yes` (đã tỉa dư thừa) |
| `tables/retention_rules.csv` | Luật `→ Churn=No` |
| `tables/churn_rule_coverage.csv` | Độ phủ thực tế của top luật churn |
| `figures/*.png` | 12 biểu đồ phân tích |

## Phương pháp

- Làm sạch `TotalCharges`, loại bản ghi thiếu cước và trùng mã khách; chuẩn hóa `SeniorCitizen`. Dữ liệu hiện tại còn 7.032 khách sau khi loại 11 bản ghi thiếu cước.
- Câu 1–2 chỉ khai phá dịch vụ có đăng ký, không trộn nhân khẩu học, hợp đồng, thanh toán hay nhãn Churn. Mặc định support ≥ 10%, confidence ≥ 70%, lift ≥ 1,2, tối đa 4 dịch vụ. Bảng xác suất ở câu 2 vẫn xuất những cặp chưa đạt ngưỡng để trả lời P(B|A) đầy đủ.
- Câu 3–4 dùng Apriori có mục tiêu; tính support trên toàn bộ khách hàng, confidence trong nhóm khớp vế trái. Tỉa luật dư thừa nếu confidence không tăng quá 2 điểm phần trăm so với luật con tổng quát hơn. Ngưỡng rời mạng là 3% / 55% / 2,0; ngưỡng ở lại là 10% / 90% / 1,2 theo thứ tự support / confidence / lift.
- Câu 5 xét tối đa 2 thuộc tính nhân khẩu học và 2–3 dịch vụ trong gói. Mỗi nhóm có ít nhất 100 khách; support toàn bộ ≥ 2%, tỷ lệ dùng gói trong nhóm ≥ 20%. Loại điện thoại cơ bản khỏi phần này để thể hiện lựa chọn gói rõ hơn. Đây là tổ hợp quan sát, không phải danh mục gói thương mại.
- Câu 6 áp dụng luật dịch vụ cho nhóm `Churn=No`, chỉ gợi ý tiện ích chưa có và đủ điều kiện Internet/điện thoại. Xếp hạng theo lift, confidence, support, rồi độ ngắn của luật. Mỗi khách tối đa 3 dịch vụ khác nhau. Nhân khẩu học và Churn không nằm trong vế trái của luật gợi ý.

Confidence là tỷ lệ đồng sử dụng quan sát, không phải xác suất mua thêm. Các luật Churn mô tả mối liên hệ; hiệu quả của ưu đãi giữ chân cần được đánh giá bằng thử nghiệm riêng. Chưa có dữ liệu giá gói để tính mức tăng doanh thu hay xác định hạng gói thương mại.

## Kiểm chứng

```bash
python -m unittest discover -s tests -v
```

Bộ kiểm thử đối chiếu Apriori với `mlxtend`, kiểm tra luật có mục tiêu bằng đếm tổ hợp độc lập, đối chiếu tỷ lệ của các câu hỏi với dữ liệu gốc và kiểm tra điều kiện áp dụng gợi ý theo khách hàng. Notebook thực thi toàn bộ luồng và hiển thị báo cáo được sinh từ kết quả thực tế.
