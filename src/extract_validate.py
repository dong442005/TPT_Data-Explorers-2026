import os
import re
import json
import email
import pdfplumber
from decimal import Decimal, InvalidOperation
from email import policy
from email.header import decode_header, make_header
from pathlib import Path

FOLDER_PATH = Path("data/raw/emails")
TEMP_DIR = Path("./temp_pdf")
OUTPUT_JSON = Path("data/processed/processed_data.json")

TEMP_DIR.mkdir(exist_ok=True)




def decode_mime_text(value):
    if not value:
        return "Unknown"
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def clean_money(value):
    if value is None:
        return Decimal("0")

    s = str(value).replace("\n", " ").strip()
    s = re.sub(r"[^\d,\.]", "", s)

    if not s:
        return Decimal("0")

    s = s.replace(".", "").replace(",", "")

    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def clean_quantity(value):
    if value is None:
        return Decimal("0")

    s = str(value).replace("\n", " ").strip()
    s = re.sub(r"[^\d,\.]", "", s)

    if not s:
        return Decimal("0")

    if "," in s and "." not in s:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def is_product_code(value):
    if value is None:
        return False

    code = str(value).strip()

    # Nhận cả:
    # - mã ERP số dài: 000104002009000
    # - mã TP có dấu chấm: TP0099.0000570
    # - mã nhóm có nhiều dấu chấm: 156.01.12.0003, TP0022.02.16.00
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\.]{5,25}", code))


def extract_email_body(msg):
    body_parts = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")

        if content_type == "text/plain" and "attachment" not in content_disposition.lower():
            try:
                body_parts.append(part.get_content())
            except Exception:
                pass

    return "\n".join(body_parts)


def extract_email_and_pdf(eml_path):
    with open(eml_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    meta = {
        "message_id": msg.get("Message-ID", "Unknown"),
        "from_address": msg.get("From", "Unknown"),
        "received_at": msg.get("Date", "Unknown"),
        "subject": decode_mime_text(msg.get("Subject", "Unknown")),
        "attachment_name": None,
        "pdf_temp_path": None,
        "email_total": "0",
        "tax_code": None,
        "customer_name_email": None,
        "order_date_email": None,
        "phone_email": None,
        "address_email": None,
    }

    body = extract_email_body(msg)

    mst_match = re.search(
        r"(?:MST|Mã\s*số\s*thuế)\s*[:：]\s*(\d{8,13})",
        body,
        flags=re.IGNORECASE
    )
    if mst_match:
        meta["tax_code"] = mst_match.group(1)

    customer_match = re.search(
        r"(?:Đại\s*lý|Khách\s*hàng|Đơn\s*vị)\s*[:：]\s*(.+)",
        body,
        flags=re.IGNORECASE
    )
    if customer_match:
        meta["customer_name_email"] = customer_match.group(1).strip()

    date_match = re.search(
        r"ngày\s*(\d{2}/\d{2}/\d{4})",
        body,
        flags=re.IGNORECASE
    )
    if date_match:
        meta["order_date_email"] = date_match.group(1)

    address_match = re.search(
        r"(?:Địa\s*chỉ)\s*[:：]\s*(.+)",
        body,
        flags=re.IGNORECASE
    )
    if address_match:
        meta["address_email"] = address_match.group(1).strip()

    phone_match = re.search(
        r"(?:Liên\s*hệ|SĐT|Điện\s*thoại)\s*[:：]\s*([\d\s\.\-]+)",
        body,
        flags=re.IGNORECASE
    )
    if phone_match:
        meta["phone_email"] = phone_match.group(1).strip()

    total_match = re.findall(
        r"(?:Tổng\s*tiền|trị\s*giá)\s*([\d\.,]+)\s*(?:đồng|VND)?",
        body,
        flags=re.IGNORECASE
    )
    if total_match:
        meta["email_total"] = str(clean_money(total_match[-1]))

    for part in msg.walk():
        filename = part.get_filename()
        content_disposition = part.get("Content-Disposition", "")

        if filename and "attachment" in content_disposition.lower() and filename.lower().endswith(".pdf"):
            pdf_filename = decode_mime_text(filename)
            safe_name = re.sub(r'[\\/:*?"<>|]', "_", pdf_filename)
            temp_path = TEMP_DIR / f"{eml_path.stem}_{safe_name}"

            payload = part.get_payload(decode=True)
            if payload:
                with open(temp_path, "wb") as pdf_file:
                    pdf_file.write(payload)

                meta["pdf_temp_path"] = str(temp_path)
                meta["attachment_name"] = pdf_filename

    return meta


def parse_pdf(pdf_path):
    lines = []
    pdf_total = Decimal("0")

    header = {
        "so_number_pdf": None,
        "order_date": None,
        "tax_code_pdf": None,
        "customer_name_pdf": None,
        "address_pdf": None,
    }

    error_message = None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()

                if not table:
                    continue

                for row in table:
                    if not row:
                        continue

                    row_text = " ".join([
                        str(x).replace("\n", " ").strip()
                        for x in row if x
                    ])

                    # Header
                    if "Số" in row_text and "hàng" in row_text:
                        match = re.search(r"BH\d{2}\.\d{4}", row_text)
                        if match:
                            header["so_number_pdf"] = match.group(0)

                    if "Ngày" in row_text:
                        match = re.search(r"\d{2}/\d{2}/\d{4}", row_text)
                        if match:
                            header["order_date"] = match.group(0)

                    if "MST" in row_text:
                        match = re.search(r"\d{8,13}", row_text)
                        if match:
                            header["tax_code_pdf"] = match.group(0)

                    if "lý" in row_text or "Đại" in row_text:
                        if len(row) >= 2 and row[1]:
                            value = str(row[1]).strip()
                            if value and "Đại" not in value:
                                header["customer_name_pdf"] = value

                    if "chỉ" in row_text:
                        if len(row) >= 2 and row[1]:
                            header["address_pdf"] = str(row[1]).strip()

                    # Total
                    if (
                        "Tổng giá trị" in row_text
                        or "Tổng tiền" in row_text
                        or "Tổng cộng" in row_text
                    ):
                        nums = re.findall(r"[\d\.,]+", row_text)
                        if nums:
                            pdf_total = clean_money(nums[-1])

                    # Product line:
                    # STT | Mã hàng | Tên sản phẩm | ĐVT | SL | Đơn giá | Thành tiền
                    if len(row) >= 7:
                        product_code = str(row[1]).strip() if row[1] else ""

                        if not is_product_code(product_code):
                            continue

                        quantity = clean_quantity(row[4])
                        unit_price = clean_money(row[5])
                        line_total = clean_money(row[6])

                        if quantity <= 0 or unit_price <= 0 or line_total <= 0:
                            continue

                        lines.append({
                            "product_code": product_code,
                            "product_name": str(row[2]).strip() if row[2] else None,
                            "unit": str(row[3]).strip() if row[3] else None,
                            "quantity": str(quantity),
                            "unit_price": str(unit_price),
                            "line_total": str(line_total),
                        })

    except Exception as e:
        error_message = str(e)

    return lines, str(pdf_total), header, error_message


def main():
    print("BẮT ĐẦU TRÍCH XUẤT VÀ CHUẨN HÓA OFFLINE...")

    if not FOLDER_PATH.exists():
        print(f"Lỗi: Không tìm thấy folder {FOLDER_PATH}")
        return

    results = {
        "ready_orders": [],
        "failed_orders": [],
        "logs": []
    }

    files = sorted([f for f in FOLDER_PATH.iterdir() if f.suffix.lower() == ".eml"])

    for idx, eml_file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Processing {eml_file.name}")

        so_number_from_file = eml_file.stem
        meta = extract_email_and_pdf(eml_file)

        base_log = {
            "message_id": meta["message_id"],
            "file": eml_file.name,
            "so_number": so_number_from_file,
            "from_address": meta["from_address"],
            "received_at": meta["received_at"],
            "attachment_name": meta["attachment_name"],
            "status": None,
            "error_message": None,
            "warning_message": None,
            "line_count": 0,
            "email_total": meta["email_total"],
            "pdf_total": "0",
            "calc_total": "0",
        }

        if not meta["pdf_temp_path"]:
            reason = "Không tìm thấy PDF attachment trong email."
            base_log["status"] = "FAILED_NO_ATTACHMENT"
            base_log["error_message"] = reason

            results["logs"].append(base_log)
            results["failed_orders"].append({
                "so_number": so_number_from_file,
                "meta": meta,
                "reason": reason,
                "lines": []
            })
            continue

        lines, pdf_total, pdf_header, parse_error = parse_pdf(meta["pdf_temp_path"])

        try:
            os.remove(meta["pdf_temp_path"])
        except OSError:
            pass

        calc_total = sum(Decimal(i["line_total"]) for i in lines)
        email_total = Decimal(meta["email_total"])
        pdf_total_decimal = Decimal(pdf_total)

        tax_code = meta["tax_code"] or pdf_header.get("tax_code_pdf")
        order_date = pdf_header.get("order_date") or meta.get("order_date_email")

        base_log["line_count"] = len(lines)
        base_log["pdf_total"] = str(pdf_total_decimal)
        base_log["calc_total"] = str(calc_total)

        reasons = []
        warnings = []

        # Chỉ fail khi không extract được dòng hàng.
        # Các lỗi tổng tiền / MST chỉ log warning để xử lý ở file insert DB.
        if not lines:
            reasons.append("Không extract được dòng sản phẩm từ PDF.")

        if parse_error:
            warnings.append(f"Lỗi phụ khi parse PDF: {parse_error}")

        if not tax_code:
            warnings.append("Thiếu MST/tax_code, file insert DB cần map bằng tên đại lý hoặc xử lý thủ công.")

        if not order_date:
            warnings.append("Thiếu order_date, file insert DB có thể lấy từ email date hoặc so_number/date khác.")

        if pdf_total_decimal <= 0:
            warnings.append("Không extract được tổng tiền PDF.")

        if pdf_total_decimal > 0 and abs(calc_total - pdf_total_decimal) > Decimal("10"):
            warnings.append(f"Lệch tổng dòng và tổng PDF: calc={calc_total}, pdf={pdf_total_decimal}")

        if email_total > 0 and pdf_total_decimal > 0 and abs(pdf_total_decimal - email_total) > Decimal("10"):
            warnings.append(f"Lệch tổng PDF và tổng email: pdf={pdf_total_decimal}, email={email_total}")

        order_payload = {
            "so_number": pdf_header.get("so_number_pdf") or so_number_from_file,
            "order_date": order_date,
            "tax_code": tax_code,
            "customer_name": (
                pdf_header.get("customer_name_pdf")
                or meta.get("customer_name_email")
            ),
            "address": (
                pdf_header.get("address_pdf")
                or meta.get("address_email")
            ),
            "meta": {
                **meta,
                "pdf_temp_path": None
            },
            "pdf_header": pdf_header,
            "lines": lines,
            "totals": {
                "email_total": str(email_total),
                "pdf_total": str(pdf_total_decimal),
                "calc_total": str(calc_total)
            },
            "warnings": warnings
        }

        if reasons:
            base_log["status"] = "PARSE_FAILED"
            base_log["error_message"] = " | ".join(reasons)
            base_log["warning_message"] = " | ".join(warnings) if warnings else None

            results["failed_orders"].append({
                **order_payload,
                "reason": base_log["error_message"]
            })
        else:
            base_log["status"] = "READY_TO_INSERT"
            base_log["warning_message"] = " | ".join(warnings) if warnings else None
            results["ready_orders"].append(order_payload)

        results["logs"].append(base_log)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=4)

    print("XONG!")
    print(f"Đã lưu vào: {OUTPUT_JSON}")
    print(f"Tổng email: {len(files)}")
    print(f"Sẵn sàng insert DB: {len(results['ready_orders'])}")
    print(f"Parse failed: {len(results['failed_orders'])}")


if __name__ == "__main__":
    main()