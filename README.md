# Telco Association Rule Mining (Apriori)

Khai phá luật kết hợp bằng thuật toán Apriori để phân tích hành vi sử dụng dịch vụ viễn thông và các yếu tố dẫn đến rời mạng trên bộ dữ liệu IBM Telco Customer Churn.

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
│   ├── visualization.py   biểu đồ
│   └── pipeline.py        luồng xử lý end-to-end & xuất kết quả
├── notebooks/telco_apriori_analysis.ipynb
├── outputs/{tables,figures}/
└── main.py
```

## Chạy

```bash
pip install -r requirements.txt
python main.py
python main.py --min-support 0.08 --min-confidence 0.75 --churn-support 0.02
jupyter notebook notebooks/telco_apriori_analysis.ipynb
```

## Kết quả

| File | Nội dung |
|---|---|
| `tables/frequent_itemsets.csv` | Tập phổ biến (hành vi dịch vụ) |
| `tables/service_rules.csv` | Luật đồng sử dụng dịch vụ |
| `tables/churn_rules.csv` | Luật `→ Churn=Yes` (đã tỉa dư thừa) |
| `tables/retention_rules.csv` | Luật `→ Churn=No` |
| `tables/churn_rule_coverage.csv` | Độ phủ thực tế của top luật churn |
| `figures/*.png` | 10 biểu đồ phân tích |
