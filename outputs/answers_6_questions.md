# Trả lời 6 câu hỏi khai phá luật kết hợp dịch vụ viễn thông

Dữ liệu: 7,043 bản ghi ban đầu; loại 11 bản ghi thiếu TotalCharges và 0 mã khách trùng. Phân tích **7,032 khách hàng**, trong đó **1,869 rời mạng (26.58%)** và **5,163 ở lại (73.42%)**.

Mỗi khách hàng là một giao dịch. Support = số khách có cả vế trái và vế phải / số khách toàn bộ; confidence = số khách có cả hai / số khách khớp vế trái; lift = confidence / tỷ lệ vế phải trên toàn bộ. Confidence phản ánh tỷ lệ quan sát trong dữ liệu này, không phải xác suất mua thêm trong tương lai. Luật rời mạng và ở lại mô tả mối liên hệ, không chứng minh quan hệ nhân quả hay hiệu quả can thiệp.

## Câu 1. Những dịch vụ nào thường được khách hàng đăng ký cùng nhau?

Có **141 tổ hợp từ 2 dịch vụ** với support ≥ 10%, xét tối đa 4 dịch vụ. Chỉ gồm dịch vụ có đăng ký; nhân khẩu học, hợp đồng, thanh toán và nhãn Churn không tham gia phần này. Các tổ hợp dưới đây được xếp theo support.

| Tổ hợp dịch vụ | Số khách | Support |
| --- | --- | --- |
| Internet Fiber optic + điện thoại | 3096 | 44.03% |
| nhiều đường dây + điện thoại | 2967 | 42.19% |
| điện thoại + phim trực tuyến | 2433 | 34.60% |
| điện thoại + truyền hình trực tuyến | 2420 | 34.41% |
| sao lưu trực tuyến + điện thoại | 2139 | 30.42% |
| bảo vệ thiết bị + điện thoại | 2115 | 30.08% |
| phim trực tuyến + truyền hình trực tuyến | 1939 | 27.57% |
| Internet Fiber optic + nhiều đường dây | 1938 | 27.56% |
| Internet Fiber optic + nhiều đường dây + điện thoại | 1938 | 27.56% |
| điện thoại + hỗ trợ kỹ thuật | 1753 | 24.93% |

Điện thoại xuất hiện trong nhiều tổ hợp vì có tỷ lệ sử dụng nền cao. Nhiều đường dây cần dịch vụ điện thoại nên tổ hợp này có tính điều kiện kỹ thuật. Để tìm gói bán chéo, xem thêm các tổ hợp không chứa điện thoại cơ bản:

| Tổ hợp dịch vụ | Số khách | Support |
| --- | --- | --- |
| phim trực tuyến + truyền hình trực tuyến | 1939 | 27.57% |
| Internet Fiber optic + nhiều đường dây | 1938 | 27.56% |
| Internet Fiber optic + phim trực tuyến | 1751 | 24.90% |
| Internet Fiber optic + truyền hình trực tuyến | 1750 | 24.89% |
| bảo vệ thiết bị + phim trực tuyến | 1594 | 22.67% |
| nhiều đường dây + phim trực tuyến | 1591 | 22.63% |
| nhiều đường dây + truyền hình trực tuyến | 1576 | 22.41% |
| bảo vệ thiết bị + truyền hình trực tuyến | 1563 | 22.23% |
| sao lưu trực tuyến + truyền hình trực tuyến | 1390 | 19.77% |
| sao lưu trực tuyến + phim trực tuyến | 1389 | 19.75% |

Chi tiết: [q1_service_bundles.csv](tables/q1_service_bundles.csv).

## Câu 2. Khi dùng dịch vụ A, khả năng dùng thêm dịch vụ B là bao nhiêu?

Tính P(B|A) trực tiếp cho mọi cặp dịch vụ thuộc hai thuộc tính khác nhau. Bảng dưới xếp theo lift, bao gồm cả các liên hệ có confidence thấp hơn ngưỡng chọn luật. Hai chiều A → B và B → A có thể có confidence khác nhau.

| Dịch vụ A | Dịch vụ B | Cùng dùng / dùng A | P(B|A) | P(B) | Lift | Đạt ngưỡng luật |
| --- | --- | --- | --- | --- | --- | --- |
| bảo mật trực tuyến | hỗ trợ kỹ thuật | 1096 / 2015 | 54.39% | 29.01% | 1.87 | Không |
| hỗ trợ kỹ thuật | bảo mật trực tuyến | 1096 / 2040 | 53.73% | 28.65% | 1.87 | Không |
| truyền hình trực tuyến | phim trực tuyến | 1939 / 2703 | 71.74% | 38.84% | 1.85 | Có |
| phim trực tuyến | truyền hình trực tuyến | 1939 / 2731 | 71.00% | 38.44% | 1.85 | Có |
| bảo vệ thiết bị | hỗ trợ kỹ thuật | 1206 / 2418 | 49.88% | 29.01% | 1.72 | Không |
| hỗ trợ kỹ thuật | bảo vệ thiết bị | 1206 / 2040 | 59.12% | 34.39% | 1.72 | Không |
| Internet DSL | bảo mật trực tuyến | 1176 / 2416 | 48.68% | 28.65% | 1.70 | Không |
| bảo mật trực tuyến | Internet DSL | 1176 / 2015 | 58.36% | 34.36% | 1.70 | Không |
| bảo vệ thiết bị | phim trực tuyến | 1594 / 2418 | 65.92% | 38.84% | 1.70 | Không |
| phim trực tuyến | bảo vệ thiết bị | 1594 / 2731 | 58.37% | 34.39% | 1.70 | Không |

Ngưỡng chọn luật dịch vụ: support ≥ 10%, confidence ≥ 70%, lift ≥ 1.2. Cột confidence trong CSV lưu tỷ lệ từ 0 đến 1. Chi tiết: [q2_service_probabilities.csv](tables/q2_service_probabilities.csv).

## Câu 3. Tổ hợp đặc điểm nào gắn với rời mạng với độ tin cậy cao?

Có **692 luật → Churn=Yes** sau tỉa dư thừa. Support ≥ 3%, confidence ≥ 55%, lift ≥ 2; tối đa 4 đặc điểm ở vế trái. Confidence được so với mức rời mạng nền 26.58%.

| Tổ hợp đặc điểm | Khớp luật | Đúng nhãn | Support | Confidence | Lift |
| --- | --- | --- | --- | --- | --- |
| có người phụ thuộc: không + Internet Fiber optic + truyền hình trực tuyến + thâm niên: 0–12 tháng | 294 | 232 | 3.30% | 78.91% | 2.97 |
| cước tháng: cao + không có bảo mật trực tuyến + không có hỗ trợ kỹ thuật + thâm niên: 0–12 tháng | 282 | 218 | 3.10% | 77.30% | 2.91 |
| Internet Fiber optic + phim trực tuyến + không có hỗ trợ kỹ thuật + thâm niên: 0–12 tháng | 288 | 222 | 3.16% | 77.08% | 2.90 |
| cước tháng: cao + hóa đơn điện tử: có + thâm niên: 0–12 tháng | 306 | 235 | 3.34% | 76.80% | 2.89 |
| Internet Fiber optic + truyền hình trực tuyến + thâm niên: 0–12 tháng | 339 | 259 | 3.68% | 76.40% | 2.87 |
| Internet Fiber optic + nhiều đường dây + thâm niên: 0–12 tháng | 377 | 286 | 4.07% | 75.86% | 2.85 |
| nhiều đường dây + không có bảo mật trực tuyến + hóa đơn điện tử: có + thâm niên: 0–12 tháng | 327 | 246 | 3.50% | 75.23% | 2.83 |
| Internet Fiber optic + phim trực tuyến + thâm niên: 0–12 tháng | 333 | 250 | 3.56% | 75.08% | 2.82 |
| Internet Fiber optic + hóa đơn điện tử: có + tổng cước: thấp | 557 | 417 | 5.93% | 74.87% | 2.82 |
| nhiều đường dây + hóa đơn điện tử: có + không có hỗ trợ kỹ thuật + thâm niên: 0–12 tháng | 328 | 245 | 3.48% | 74.70% | 2.81 |

Ưu tiên khảo sát chất lượng dịch vụ và hỗ trợ sớm cho nhóm khớp các luật rủi ro. Luật có thể chồng lấn; không cộng số khách giữa các dòng. Độ phủ hợp của các luật nằm trong churn_rule_coverage.csv. Chi tiết: [q3_churn_patterns.csv](tables/q3_churn_patterns.csv).

## Câu 4. Tổ hợp đặc điểm nào gắn với khách hàng ở lại?

Có **24 luật → Churn=No** sau tỉa dư thừa. Support ≥ 10%, confidence ≥ 90%, lift ≥ 1.2. Mức ở lại nền là 73.42%.

| Tổ hợp đặc điểm | Khớp luật | Đúng nhãn | Support | Confidence | Lift |
| --- | --- | --- | --- | --- | --- |
| cước tháng: thấp + điện thoại + tổng cước: trung bình | 740 | 721 | 10.25% | 97.43% | 1.33 |
| hợp đồng: 2 năm | 1685 | 1637 | 23.28% | 97.15% | 1.32 |
| không dùng Internet + có bạn đời: có | 733 | 704 | 10.01% | 96.04% | 1.31 |
| Internet DSL + thâm niên: 49–72 tháng | 788 | 754 | 10.72% | 95.69% | 1.30 |
| Internet DSL + tổng cước: cao | 820 | 783 | 11.13% | 95.49% | 1.30 |
| cước tháng: thấp + tổng cước: trung bình | 959 | 906 | 12.88% | 94.47% | 1.29 |
| hóa đơn điện tử: không + thâm niên: 49–72 tháng | 902 | 852 | 12.12% | 94.46% | 1.29 |
| có người phụ thuộc: có + thâm niên: 49–72 tháng | 853 | 801 | 11.39% | 93.90% | 1.28 |
| cước tháng: thấp + có bạn đời: có + điện thoại | 818 | 767 | 10.91% | 93.77% | 1.28 |
| hỗ trợ kỹ thuật + thâm niên: 49–72 tháng | 1053 | 984 | 13.99% | 93.45% | 1.27 |

Có thể thiết kế thử nghiệm ưu đãi hợp đồng dài hạn và gói hỗ trợ phù hợp. Dữ liệu hiện tại chưa chứng minh việc chuyển hợp đồng hay thêm dịch vụ sẽ làm giảm churn. Chi tiết: [q4_retention_patterns.csv](tables/q4_retention_patterns.csv).

## Câu 5. Nhóm khách hàng theo nhân khẩu học thường chọn gói dịch vụ nào?

Xét giới tính, cao tuổi, có bạn đời và người phụ thuộc, tối đa 2 đặc điểm một nhóm. Mỗi nhóm có ít nhất 100 khách; gói gồm 2–3 dịch vụ, support toàn bộ ≥ 2%, tỷ lệ dùng trong nhóm ≥ 20%. Điện thoại cơ bản được loại khỏi gói ở câu này để thấy lựa chọn dịch vụ rõ hơn. Tên gói là tổ hợp dịch vụ quan sát được, không phải danh mục gói thương mại có sẵn.

Tổ hợp phổ biến nhất cho từng nhóm một đặc điểm:

| Nhóm | Tổ hợp dịch vụ | Dùng gói / số khách nhóm | Tỷ lệ trong nhóm | Toàn bộ dữ liệu | Lift |
| --- | --- | --- | --- | --- | --- |
| có người phụ thuộc: không | Internet Fiber optic + nhiều đường dây | 1512 / 4933 | 30.65% | 27.56% | 1.11 |
| có người phụ thuộc: có | phim trực tuyến + truyền hình trực tuyến | 554 / 2099 | 26.39% | 27.57% | 0.96 |
| có bạn đời: không | Internet Fiber optic + nhiều đường dây | 897 / 3639 | 24.65% | 27.56% | 0.89 |
| có bạn đời: có | phim trực tuyến + truyền hình trực tuyến | 1134 / 3393 | 33.42% | 27.57% | 1.21 |
| cao tuổi: không | phim trực tuyến + truyền hình trực tuyến | 1513 / 5890 | 25.69% | 27.57% | 0.93 |
| cao tuổi: có | Internet Fiber optic + nhiều đường dây | 568 / 1142 | 49.74% | 27.56% | 1.80 |
| giới tính: nữ | phim trực tuyến + truyền hình trực tuyến | 974 / 3483 | 27.96% | 27.57% | 1.01 |
| giới tính: nam | Internet Fiber optic + nhiều đường dây | 974 / 3549 | 27.44% | 27.56% | 1.00 |

Các tổ hợp nhóm và dịch vụ khác biệt nhất so với toàn bộ dữ liệu (xếp theo lift):

| Nhóm | Tổ hợp dịch vụ | Dùng gói / số khách nhóm | Tỷ lệ trong nhóm | Toàn bộ dữ liệu | Lift |
| --- | --- | --- | --- | --- | --- |
| có bạn đời: có + cao tuổi: có | Internet Fiber optic + nhiều đường dây + phim trực tuyến | 216 / 573 | 37.70% | 17.48% | 2.16 |
| có bạn đời: có + cao tuổi: có | bảo vệ thiết bị + Internet Fiber optic + nhiều đường dây | 168 / 573 | 29.32% | 13.72% | 2.14 |
| có bạn đời: có + cao tuổi: có | Internet Fiber optic + sao lưu trực tuyến + phim trực tuyến | 148 / 573 | 25.83% | 12.51% | 2.06 |
| có bạn đời: có + cao tuổi: có | Internet Fiber optic + nhiều đường dây + sao lưu trực tuyến | 162 / 573 | 28.27% | 13.72% | 2.06 |
| có bạn đời: có + cao tuổi: có | Internet Fiber optic + nhiều đường dây + truyền hình trực tuyến | 204 / 573 | 35.60% | 17.43% | 2.04 |
| có bạn đời: có + cao tuổi: có | bảo vệ thiết bị + Internet Fiber optic + truyền hình trực tuyến | 158 / 573 | 27.57% | 13.72% | 2.01 |
| có bạn đời: có + cao tuổi: có | bảo vệ thiết bị + Internet Fiber optic + phim trực tuyến | 158 / 573 | 27.57% | 13.75% | 2.01 |
| có bạn đời: có + cao tuổi: có | Internet Fiber optic + nhiều đường dây | 313 / 573 | 54.62% | 27.56% | 1.98 |
| có bạn đời: có + cao tuổi: có | nhiều đường dây + sao lưu trực tuyến + phim trực tuyến | 143 / 573 | 24.96% | 12.76% | 1.96 |
| có bạn đời: có + cao tuổi: có | nhiều đường dây + phim trực tuyến + truyền hình trực tuyến | 190 / 573 | 33.16% | 17.19% | 1.93 |

Các nhóm có thể giao nhau. Chọn gói theo nhu cầu và điều kiện dịch vụ thực tế; nhân khẩu học chỉ dùng để mô tả nhóm. Chi tiết: [q5_demographic_bundles.csv](tables/q5_demographic_bundles.csv).

## Câu 6. Có thể xây dựng gợi ý nâng cấp gói từ các luật tìm được không?

Có. **74 luật có khách đủ điều kiện** tạo **3,005 gợi ý** cho **2,062 khách** trong 5,163 khách Churn=No. Mỗi khách nhận tối đa 3 dịch vụ bổ sung khác nhau.

Chỉ dùng các dịch vụ đã đăng ký ở vế trái và một dịch vụ bổ sung ở vế phải; khách chưa có dịch vụ được gợi ý, có Internet nếu là tiện ích Internet hoặc có điện thoại nếu thêm nhiều đường dây. Xếp hạng theo lift, confidence, support rồi ưu tiên luật ngắn khi hòa điểm. Churn=No chỉ xác định nhóm minh họa còn ở lại; không dùng làm điều kiện dự đoán mua thêm.

| Luật gợi ý | Confidence | Lift | Khách đủ điều kiện | Được chọn theo luật |
| --- | --- | --- | --- | --- |
| phim trực tuyến + truyền hình trực tuyến + hỗ trợ kỹ thuật → bảo vệ thiết bị | 74.68% | 2.17 | 183 | 183 |
| bảo vệ thiết bị + truyền hình trực tuyến + hỗ trợ kỹ thuật → phim trực tuyến | 83.83% | 2.16 | 124 | 124 |
| bảo vệ thiết bị + nhiều đường dây + phim trực tuyến → truyền hình trực tuyến | 82.91% | 2.16 | 138 | 138 |
| bảo vệ thiết bị + Internet Fiber optic + phim trực tuyến → truyền hình trực tuyến | 82.83% | 2.15 | 123 | 46 |
| bảo vệ thiết bị + nhiều đường dây + truyền hình trực tuyến → phim trực tuyến | 83.50% | 2.15 | 131 | 71 |
| bảo vệ thiết bị + Internet Fiber optic + truyền hình trực tuyến → phim trực tuyến | 83.01% | 2.14 | 114 | 22 |
| bảo vệ thiết bị + phim trực tuyến + hỗ trợ kỹ thuật → truyền hình trực tuyến | 81.50% | 2.12 | 143 | 51 |
| bảo vệ thiết bị + sao lưu trực tuyến + phim trực tuyến → truyền hình trực tuyến | 80.96% | 2.11 | 151 | 16 |
| bảo vệ thiết bị + sao lưu trực tuyến + truyền hình trực tuyến → phim trực tuyến | 81.59% | 2.10 | 140 | 14 |
| bảo vệ thiết bị + truyền hình trực tuyến → phim trực tuyến | 80.17% | 2.06 | 247 | 16 |

Ví dụ gợi ý theo khách hàng:

| Mã khách | Hạng | Dịch vụ nên giới thiệu | Căn cứ | Luật |
| --- | --- | --- | --- | --- |
| 0002-ORFBO | 1 | phim trực tuyến | điện thoại + truyền hình trực tuyến + hỗ trợ kỹ thuật | UP0019 |
| 0002-ORFBO | 2 | nhiều đường dây | sao lưu trực tuyến + điện thoại + truyền hình trực tuyến | UP0063 |
| 0003-MKNFE | 1 | truyền hình trực tuyến | nhiều đường dây + phim trực tuyến | UP0025 |
| 0013-MHZWF | 1 | bảo vệ thiết bị | phim trực tuyến + truyền hình trực tuyến + hỗ trợ kỹ thuật | UP0001 |
| 0013-SMEOE | 1 | nhiều đường dây | bảo vệ thiết bị + Internet Fiber optic + truyền hình trực tuyến | UP0059 |
| 0014-BMAQU | 1 | phim trực tuyến | nhiều đường dây + hỗ trợ kỹ thuật | UP0056 |
| 0017-DINOC | 1 | phim trực tuyến | truyền hình trực tuyến + hỗ trợ kỹ thuật | UP0022 |
| 0019-EFAEP | 1 | phim trực tuyến | bảo vệ thiết bị + nhiều đường dây + truyền hình trực tuyến | UP0005 |
| 0019-GFNTW | 1 | phim trực tuyến | bảo vệ thiết bị + hỗ trợ kỹ thuật | UP0052 |
| 0020-INWCK | 1 | truyền hình trực tuyến | bảo vệ thiết bị + nhiều đường dây + phim trực tuyến | UP0003 |

Đây là gợi ý bán chéo dịch vụ dựa trên đồng sử dụng, chưa xác định gói giá cao hơn, doanh thu tăng thêm hay xác suất chấp nhận ưu đãi. Cần dữ liệu giá gói, lịch sử mua và thử nghiệm A/B để đánh giá chuyển đổi và giữ chân. Chi tiết: [q6_upgrade_rules.csv](tables/q6_upgrade_rules.csv), [q6_customer_recommendations.csv](tables/q6_customer_recommendations.csv).

## Cách đọc và tái lập kết quả

Chạy `python main.py` từ thư mục dự án. `--top` chỉ thay đổi số dòng trình bày; CSV luôn chứa toàn bộ kết quả thỏa điều kiện. `--no-figures` bỏ bước tạo biểu đồ. Các tham số, dấu vân tay SHA-256 của dữ liệu, ngưỡng chia nhóm cước và số lượng đầu ra được lưu trong [run_metadata.json](run_metadata.json).

MonthlyCharges và TotalCharges được chia ba phân vị trên dữ liệu đã làm sạch; thâm niên chia 0–12, 13–24, 25–48, 49–72 tháng. Tỉa luật churn/ở lại giữ luật có confidence cao hơn mọi luật con được xét trên cùng tập nhãn quá 2 điểm phần trăm theo cấu hình mặc định. Các tỷ lệ là mô tả trên dữ liệu dùng khai phá, chưa phải đánh giá trên tập kiểm định độc lập. Những khách mới thiếu TotalCharges đã bị loại nên kết quả không đại diện đầy đủ cho nhóm thâm niên 0 tháng.
