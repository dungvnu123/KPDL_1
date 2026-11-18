import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import pandas as pd

if TYPE_CHECKING:
    from .pipeline import PipelineResult


SERVICE_LABELS = {
    "PhoneService": "điện thoại", "MultipleLines": "nhiều đường dây",
    "OnlineSecurity": "bảo mật trực tuyến", "OnlineBackup": "sao lưu trực tuyến",
    "DeviceProtection": "bảo vệ thiết bị", "TechSupport": "hỗ trợ kỹ thuật",
    "StreamingTV": "truyền hình trực tuyến", "StreamingMovies": "phim trực tuyến",
}
FEATURE_LABELS = {
    "gender": "giới tính", "SeniorCitizen": "cao tuổi", "Partner": "có bạn đời",
    "Dependents": "có người phụ thuộc", "Contract": "hợp đồng", "PaymentMethod": "thanh toán",
    "PaperlessBilling": "hóa đơn điện tử", "TenureGroup": "thâm niên",
    "MonthlyCharges": "cước tháng", "TotalCharges": "tổng cước",
}
VALUE_LABELS = {
    "Yes": "có", "No": "không", "Male": "nam", "Female": "nữ",
    "Month-to-month": "từng tháng", "One year": "1 năm", "Two year": "2 năm",
    "Electronic check": "séc điện tử", "Mailed check": "séc gửi bưu điện",
    "Bank transfer (automatic)": "chuyển khoản tự động",
    "Credit card (automatic)": "thẻ tín dụng tự động",
    "Low": "thấp", "Medium": "trung bình", "High": "cao",
    "0-12m": "0–12 tháng", "13-24m": "13–24 tháng",
    "25-48m": "25–48 tháng", "49-72m": "49–72 tháng",
}


def describe_items(items: str) -> str:
    labels = []
    for item in items.split(", "):
        column, value = item.split("=", 1)
        if column in SERVICE_LABELS:
            label = SERVICE_LABELS[column]
            labels.append(label if value == "Yes" else f"không có {label}")
        elif column == "InternetService":
            labels.append("không dùng Internet" if value == "No" else f"Internet {value}")
        else:
            labels.append(f"{FEATURE_LABELS.get(column, column)}: {VALUE_LABELS.get(value, value)}")
    return " + ".join(labels)


def _percent(value: float) -> str:
    return f"{value:.2%}"


def _table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    materialized = [list(row) for row in rows]
    if not materialized:
        return "Không có kết quả thỏa các ngưỡng hiện tại."
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in row) + " |"
                 for row in materialized)
    return "\n".join(lines)


def _target_table(table: pd.DataFrame, top: int) -> str:
    return _table(
        ["Tổ hợp đặc điểm", "Khớp luật", "Đúng nhãn", "Support", "Confidence", "Lift"],
        ([describe_items(row.antecedents), row.matched_customers, row.target_customers,
          _percent(row.support), _percent(row.confidence), f"{row.lift:.2f}"]
         for row in table.head(top).itertuples()),
    )


def _demographic_table(table: pd.DataFrame, top: int) -> str:
    return _table(
        ["Nhóm", "Tổ hợp dịch vụ", "Dùng gói / số khách nhóm", "Tỷ lệ trong nhóm", "Toàn bộ dữ liệu", "Lift"],
        ([describe_items(row.demographics), describe_items(row.bundle),
          f"{row.bundle_customers} / {row.group_customers}", _percent(row.confidence),
          _percent(row.baseline_bundle), f"{row.lift:.2f}"] for row in table.head(top).itertuples()),
    )


def render_report(result: "PipelineResult", top: int = 10) -> str:
    if top < 1:
        raise ValueError("top must be at least 1")
    answers, settings = result.answers, result.settings
    quality = result.customers.attrs["quality"]
    n = len(result.customers)
    churn_count = int(result.customers[settings.features.target_column].eq("Yes").sum())
    sections = [
        "# Trả lời 6 câu hỏi khai phá luật kết hợp dịch vụ viễn thông",
        f"Dữ liệu: {quality['raw_customers']:,} bản ghi ban đầu; loại {quality['missing_total_charges_removed']} "
        f"bản ghi thiếu TotalCharges và {quality['duplicate_ids_removed']} mã khách trùng. "
        f"Phân tích **{n:,} khách hàng**, trong đó **{churn_count:,} rời mạng ({result.churn_rate:.2%})** "
        f"và **{n - churn_count:,} ở lại ({1 - result.churn_rate:.2%})**.",
        "Mỗi khách hàng là một giao dịch. Support = số khách có cả vế trái và vế phải / số khách toàn bộ; "
        "confidence = số khách có cả hai / số khách khớp vế trái; lift = confidence / tỷ lệ vế phải trên toàn bộ. "
        "Confidence phản ánh tỷ lệ quan sát trong dữ liệu này, không phải xác suất mua thêm trong tương lai. "
        "Luật rời mạng và ở lại mô tả mối liên hệ, không chứng minh quan hệ nhân quả hay hiệu quả can thiệp.",
        "## Câu 1. Những dịch vụ nào thường được khách hàng đăng ký cùng nhau?",
        f"Có **{len(answers.bundles)} tổ hợp từ 2 dịch vụ** với support ≥ {settings.mining.min_support:.0%}, "
        f"xét tối đa {settings.mining.max_len} dịch vụ. Chỉ gồm dịch vụ có đăng ký; "
        "nhân khẩu học, hợp đồng, thanh toán và nhãn Churn không tham gia phần này. "
        "Các tổ hợp dưới đây được xếp theo support.",
        _table(["Tổ hợp dịch vụ", "Số khách", "Support"],
               ([describe_items(r.itemsets), r.customers, _percent(r.support)]
                for r in answers.bundles.head(top).itertuples())),
        "Điện thoại xuất hiện trong nhiều tổ hợp vì có tỷ lệ sử dụng nền cao. "
        "Nhiều đường dây cần dịch vụ điện thoại nên tổ hợp này có tính điều kiện kỹ thuật. "
        "Để tìm gói bán chéo, xem thêm các tổ hợp không chứa điện thoại cơ bản:",
        _table(["Tổ hợp dịch vụ", "Số khách", "Support"],
               ([describe_items(r.itemsets), r.customers, _percent(r.support)]
                for r in answers.bundles.loc[
                    ~answers.bundles["itemsets"].str.contains("PhoneService=Yes", regex=False)
                ].head(top).itertuples())),
        "Chi tiết: [q1_service_bundles.csv](tables/q1_service_bundles.csv).",
        "## Câu 2. Khi dùng dịch vụ A, khả năng dùng thêm dịch vụ B là bao nhiêu?",
        "Tính P(B|A) trực tiếp cho mọi cặp dịch vụ thuộc hai thuộc tính khác nhau. "
        "Bảng dưới xếp theo lift, bao gồm cả các liên hệ có confidence thấp hơn ngưỡng chọn luật. "
        "Hai chiều A → B và B → A có thể có confidence khác nhau.",
        _table(["Dịch vụ A", "Dịch vụ B", "Cùng dùng / dùng A", "P(B|A)", "P(B)", "Lift", "Đạt ngưỡng luật"],
               ([describe_items(r.service_a), describe_items(r.service_b),
                 f"{r.both_customers} / {r.a_customers}", _percent(r.confidence), _percent(r.baseline_b),
                 f"{r.lift:.2f}", "Có" if r.passes_thresholds else "Không"]
                for r in answers.probabilities.loc[~answers.probabilities["is_prerequisite"]].head(top).itertuples())),
        f"Ngưỡng chọn luật dịch vụ: support ≥ {settings.mining.min_support:.0%}, "
        f"confidence ≥ {settings.mining.min_confidence:.0%}, lift ≥ {settings.mining.min_lift:g}. "
        "Cột confidence trong CSV lưu tỷ lệ từ 0 đến 1. "
        "Chi tiết: [q2_service_probabilities.csv](tables/q2_service_probabilities.csv).",
        "## Câu 3. Tổ hợp đặc điểm nào gắn với rời mạng với độ tin cậy cao?",
        f"Có **{len(answers.churn)} luật → Churn=Yes** sau tỉa dư thừa. "
        f"Support ≥ {settings.churn.min_support:.0%}, confidence ≥ {settings.churn.min_confidence:.0%}, "
        f"lift ≥ {settings.churn.min_lift:g}; tối đa {settings.churn.max_len - 1} đặc điểm ở vế trái. "
        f"Confidence được so với mức rời mạng nền {result.churn_rate:.2%}.",
        _target_table(answers.churn, top),
        "Ưu tiên khảo sát chất lượng dịch vụ và hỗ trợ sớm cho nhóm khớp các luật rủi ro. "
        "Luật có thể chồng lấn; không cộng số khách giữa các dòng. "
        "Độ phủ hợp của các luật nằm trong churn_rule_coverage.csv. "
        "Chi tiết: [q3_churn_patterns.csv](tables/q3_churn_patterns.csv).",
        "## Câu 4. Tổ hợp đặc điểm nào gắn với khách hàng ở lại?",
        f"Có **{len(answers.retention)} luật → Churn=No** sau tỉa dư thừa. "
        f"Support ≥ {settings.retention.min_support:.0%}, confidence ≥ {settings.retention.min_confidence:.0%}, "
        f"lift ≥ {settings.retention.min_lift:g}. Mức ở lại nền là {1 - result.churn_rate:.2%}.",
        _target_table(answers.retention, top),
        "Có thể thiết kế thử nghiệm ưu đãi hợp đồng dài hạn và gói hỗ trợ phù hợp. "
        "Dữ liệu hiện tại chưa chứng minh việc chuyển hợp đồng hay thêm dịch vụ sẽ làm giảm churn. "
        "Chi tiết: [q4_retention_patterns.csv](tables/q4_retention_patterns.csv).",
        "## Câu 5. Nhóm khách hàng theo nhân khẩu học thường chọn gói dịch vụ nào?",
        f"Xét giới tính, cao tuổi, có bạn đời và người phụ thuộc, tối đa "
        f"{settings.questions.max_demographic_len} đặc điểm một nhóm. Mỗi nhóm có ít nhất "
        f"{settings.questions.min_group_customers} khách; gói gồm 2–{settings.questions.max_bundle_len} dịch vụ, "
        f"support toàn bộ ≥ {settings.questions.demographic_support:.0%}, "
        f"tỷ lệ dùng trong nhóm ≥ {settings.questions.demographic_confidence:.0%}. "
        "Điện thoại cơ bản được loại khỏi gói ở câu này để thấy lựa chọn dịch vụ rõ hơn. "
        "Tên gói là tổ hợp dịch vụ quan sát được, không phải danh mục gói thương mại có sẵn.",
        "Tổ hợp phổ biến nhất cho từng nhóm một đặc điểm:",
        _demographic_table(answers.demographics.loc[answers.demographics["demographic_len"] == 1]
                           .drop_duplicates("demographics"), max(top, 8)),
        "Các tổ hợp nhóm và dịch vụ khác biệt nhất so với toàn bộ dữ liệu (xếp theo lift):",
        _demographic_table(answers.demographics.sort_values(
            ["lift", "confidence", "demographics", "bundle"], ascending=[False, False, True, True]
        ), top),
        "Các nhóm có thể giao nhau. Chọn gói theo nhu cầu và điều kiện dịch vụ thực tế; "
        "nhân khẩu học chỉ dùng để mô tả nhóm. Chi tiết: [q5_demographic_bundles.csv](tables/q5_demographic_bundles.csv).",
        "## Câu 6. Có thể xây dựng gợi ý nâng cấp gói từ các luật tìm được không?",
    ]
    recommendations = answers.recommendations
    id_column = settings.features.id_column
    eligible_rules = answers.upgrade_rules.loc[answers.upgrade_rules["eligible_customers"] > 0]
    if recommendations.empty:
        sections.append("Chưa có gợi ý hợp lệ với các ngưỡng và điều kiện hiện tại. "
                        "Các bảng gợi ý vẫn được xuất kèm tiêu đề cột để kiểm tra.")
    else:
        sections.append(
            f"Có. **{len(eligible_rules)} luật có khách đủ điều kiện** tạo **{len(recommendations):,} gợi ý** "
            f"cho **{recommendations[id_column].nunique():,} khách** trong {n - churn_count:,} khách Churn=No. "
            f"Mỗi khách nhận tối đa {settings.questions.recommendations_per_customer} dịch vụ bổ sung khác nhau."
        )
    sections.extend([
        "Chỉ dùng các dịch vụ đã đăng ký ở vế trái và một dịch vụ bổ sung ở vế phải; "
        "khách chưa có dịch vụ được gợi ý, có Internet nếu là tiện ích Internet hoặc có điện thoại nếu thêm nhiều đường dây. "
        "Xếp hạng theo lift, confidence, support rồi ưu tiên luật ngắn khi hòa điểm. "
        "Churn=No chỉ xác định nhóm minh họa còn ở lại; không dùng làm điều kiện dự đoán mua thêm.",
        _table(["Luật gợi ý", "Confidence", "Lift", "Khách đủ điều kiện", "Được chọn theo luật"],
               ([f"{describe_items(r.antecedents)} → {describe_items(r.consequents)}", _percent(r.confidence),
                 f"{r.lift:.2f}", r.eligible_customers, r.selected_customers]
                for r in eligible_rules.head(top).itertuples())),
        "Ví dụ gợi ý theo khách hàng:",
        _table(["Mã khách", "Hạng", "Dịch vụ nên giới thiệu", "Căn cứ", "Luật"],
               ([getattr(r, id_column), r.rank, describe_items(r.recommended_service),
                 describe_items(r.matched_services), r.rule_id]
                for r in recommendations.sort_values([id_column, "rank"]).head(top).itertuples())),
        "Đây là gợi ý bán chéo dịch vụ dựa trên đồng sử dụng, chưa xác định gói giá cao hơn, "
        "doanh thu tăng thêm hay xác suất chấp nhận ưu đãi. Cần dữ liệu giá gói, lịch sử mua và thử nghiệm "
        "A/B để đánh giá chuyển đổi và giữ chân. "
        "Chi tiết: [q6_upgrade_rules.csv](tables/q6_upgrade_rules.csv), "
        "[q6_customer_recommendations.csv](tables/q6_customer_recommendations.csv).",
        "## Cách đọc và tái lập kết quả",
        "Chạy `python main.py` từ thư mục dự án. `--top` chỉ thay đổi số dòng trình bày; "
        "CSV luôn chứa toàn bộ kết quả thỏa điều kiện. `--no-figures` bỏ bước tạo biểu đồ. "
        "Các tham số, dấu vân tay SHA-256 của dữ liệu, ngưỡng chia nhóm cước và số lượng đầu ra "
        "được lưu trong [run_metadata.json](run_metadata.json).",
        "MonthlyCharges và TotalCharges được chia ba phân vị trên dữ liệu đã làm sạch; "
        "thâm niên chia 0–12, 13–24, 25–48, 49–72 tháng. Tỉa luật churn/ở lại giữ luật "
        "có confidence cao hơn mọi luật con được xét trên cùng tập nhãn quá 2 điểm phần trăm theo cấu hình mặc định. "
        "Các tỷ lệ là mô tả trên dữ liệu dùng khai phá, chưa phải đánh giá trên tập kiểm định độc lập. "
        "Những khách mới thiếu TotalCharges đã bị loại nên kết quả không đại diện đầy đủ cho nhóm thâm niên 0 tháng.",
    ])
    return "\n\n".join(sections) + "\n"


def export_report(result: "PipelineResult", directory: Path, top: int = 10) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / "answers_6_questions.md"
    report_path.write_text(render_report(result, top), encoding="utf-8")
    source = result.settings.paths.raw_data
    charge_bins = {
        column: pd.qcut(result.customers[column], q=len(result.settings.features.charge_labels), retbins=True)[1].tolist()
        for column in ("MonthlyCharges", "TotalCharges")
    }
    metadata = {
        "source": str(source.resolve()), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "settings": asdict(result.settings), "data_quality": result.customers.attrs["quality"],
        "churn_rate": result.churn_rate, "charge_bin_edges": charge_bins,
        "table_rows": {name: len(table) for name, table in result.answers.tables().items()},
    }
    metadata_path = directory / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return [report_path, metadata_path]
