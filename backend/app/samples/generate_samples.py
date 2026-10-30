from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
rng = random.Random(42)


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def students() -> None:
    headers = [
        "Student_ID",
        "Name",
        "Email",
        "City",
        "Age",
        "Math",
        "Science",
        "English",
        "Total_Marks",
        "Enrollment_Date",
        "Graduation_Date",
        "Passed",
    ]
    cities = ["Jaipur", "Mumbai", "Delhi", "Pune", "Bengaluru"]
    names = ["Asha", "Rohan", "Mia", "Kabir", "Leela", "Noah", "Priya", "Arjun"]
    rows = []
    truth = []
    for i in range(600):
        sid = f"S{i:04d}"
        name = names[i % len(names)] + " " + rng.choice(["Sharma", "Patel", "Khan", "Iyer"])
        email = f"{name.split()[0].lower()}{i}@school.edu"
        city = cities[i % len(cities)]
        age = str(rng.randint(16, 22))
        math, sci, eng = rng.randint(40, 95), rng.randint(40, 95), rng.randint(40, 95)
        total = math + sci + eng
        enr = f"{rng.randint(1,28):02d}/10/2024"
        grad = "15/05/2026"
        passed = rng.choice(["Yes", "No"])
        row = [sid, name, email, city, age, str(math), str(sci), str(eng), str(total), enr, grad, passed]
        rid = i
        if i == 10:
            row[4] = ""
            truth.append({"id": "blank_age", "type": "missing_value", "rid": rid, "column": "Age", "clean_value": "18", "dirty_value": "", "correct_fix": "leave_or_fill"})
        if i == 11:
            row[4] = "twenty"
            truth.append({"id": "age_twenty", "type": "invalid_numeric", "rid": rid, "column": "Age", "clean_value": "20", "dirty_value": "twenty", "correct_fix": "20"})
        if i == 12:
            row[4] = "nineteen"
            truth.append({"id": "age_nineteen", "type": "invalid_numeric", "rid": rid, "column": "Age", "clean_value": "19", "dirty_value": "nineteen", "correct_fix": "19"})
        if i == 13:
            row[3] = " Jaipur "
            truth.append({"id": "ws_city", "type": "inconsistent_text", "rid": rid, "column": "City", "clean_value": "Jaipur", "dirty_value": " Jaipur ", "correct_fix": "Jaipur"})
        if i == 14:
            row[3] = "jaipur"
            truth.append({"id": "case_city", "type": "inconsistent_text", "rid": rid, "column": "City", "clean_value": "Jaipur", "dirty_value": "jaipur", "correct_fix": "Jaipur"})
        if i == 15:
            row[3] = "JAIPUR"
        if i == 16:
            row[3] = "Japur"
            truth.append({"id": "typo_city", "type": "inconsistent_text", "rid": rid, "column": "City", "clean_value": "Jaipur", "dirty_value": "Japur", "correct_fix": "review"})
        if i == 17:
            row[3] = "Jaipur "
        if i == 20:
            row[4] = "N/A"
            truth.append({"id": "na_age", "type": "missing_value", "rid": rid, "column": "Age", "clean_value": "", "dirty_value": "N/A", "correct_fix": "blank"})
        if i == 21:
            row[5] = "-"
        if i == 30:
            row[9] = "2024-10-25"
            truth.append({"id": "date_iso", "type": "inconsistent_format", "rid": rid, "column": "Enrollment_Date", "clean_value": "2024-10-25", "dirty_value": "2024-10-25", "correct_fix": "standardize"})
        if i == 31:
            row[9] = "25 Oct 2024"
        if i == 40:
            row[5] = "105"
            truth.append({"id": "marks_over", "type": "invalid_value", "rid": rid, "column": "Math", "clean_value": "", "dirty_value": "105", "correct_fix": "rule"})
        if i == 41:
            row[4] = "212"
            truth.append({"id": "age_outlier", "type": "outlier", "rid": rid, "column": "Age", "clean_value": "212", "dirty_value": "212", "correct_fix": "keep"})
        if i == 50:
            row[8] = str(total + 15)
            truth.append({"id": "total_mismatch", "type": "invalid_value", "rid": rid, "column": "Total_Marks", "clean_value": str(total), "dirty_value": row[8], "correct_fix": "recompute"})
        if i == 51:
            row[10] = "01/01/2024"
            truth.append({"id": "grad_before", "type": "invalid_value", "rid": rid, "column": "Graduation_Date", "clean_value": grad, "dirty_value": row[10], "correct_fix": "review"})
        if i == 52:
            row[2] = "not-an-email"
            truth.append({"id": "bad_email", "type": "invalid_value", "rid": rid, "column": "Email", "clean_value": email, "dirty_value": "not-an-email", "correct_fix": "review"})
        if i == 53:
            row[6] = "9999"
            truth.append({"id": "sci_outlier", "type": "outlier", "rid": rid, "column": "Science", "clean_value": "9999", "dirty_value": "9999", "correct_fix": "keep"})
        if i == 54:
            row[11] = "Y"
        if i == 55:
            row[11] = "true"
        if i == 60:
            row[0] = "S0001"
            truth.append({"id": "dup_id", "type": "duplicate_id", "rid": rid, "column": "Student_ID", "clean_value": sid, "dirty_value": "S0001", "correct_fix": "review"})
        rows.append(row)
    # exact duplicate of row 5
    rows.append(list(rows[5]))
    truth.append({"id": "dup_row", "type": "duplicate_row", "rid": 600, "column": "*", "clean_value": "", "dirty_value": "copy", "correct_fix": "delete"})
    write_csv(ROOT / "students_messy.csv", headers, rows)
    (ROOT / "students_messy.truth.json").write_text(json.dumps(truth, indent=2))


def sales() -> None:
    headers = ["Order_ID", "Customer", "Region", "Product", "Quantity", "Unit_Price", "Total_Price", "Order_Date", "Ship_Date", "Status"]
    rows = []
    truth = []
    for i in range(1200):
        oid = f"O{i:05d}"
        cust = rng.choice(["Rahul Sharma", "Anita Desai", "Mia Chen", "Omar Ali"])
        region = rng.choice(["North", "South", "East", "West"])
        product = rng.choice(["Lamp", "Chair", "Desk", "Mug"])
        qty = rng.randint(1, 20)
        price = rng.choice([199, 349, 499, 1200])
        total = qty * price
        od = f"{rng.randint(1,28):02d}/09/2026"
        sd = f"{rng.randint(1,28):02d}/10/2026"
        status = rng.choice(["Shipped", "Pending", "Cancelled"])
        row = [oid, cust, region, product, str(qty), str(price), str(total), od, sd, status]
        if i == 7:
            row[4] = "-3"
            truth.append({"id": "neg_qty", "type": "invalid_value", "rid": i, "column": "Quantity", "clean_value": "3", "dirty_value": "-3", "correct_fix": "review"})
        if i == 8:
            row[4] = "100000"
            truth.append({"id": "qty_out", "type": "outlier", "rid": i, "column": "Quantity", "clean_value": "100000", "dirty_value": "100000", "correct_fix": "keep"})
        if i == 9:
            row[7] = "31/02/2026"
            truth.append({"id": "bad_date", "type": "invalid_value", "rid": i, "column": "Order_Date", "clean_value": "", "dirty_value": "31/02/2026", "correct_fix": "manual"})
        if i == 10:
            row[6] = str(total + 50)
            truth.append({"id": "price_mismatch", "type": "invalid_value", "rid": i, "column": "Total_Price", "clean_value": str(total), "dirty_value": row[6], "correct_fix": "recompute"})
        if i == 11:
            row[8] = "01/01/2026"
            truth.append({"id": "ship_before", "type": "invalid_value", "rid": i, "column": "Ship_Date", "clean_value": sd, "dirty_value": row[8], "correct_fix": "review"})
        if i == 12:
            row[5] = "₹1,200"
            truth.append({"id": "currency", "type": "inconsistent_format", "rid": i, "column": "Unit_Price", "clean_value": "1200", "dirty_value": "₹1,200", "correct_fix": "1200"})
        if i == 13:
            row[5] = "1,200"
        if i == 14:
            row[1] = "Rahul Sharmaa"
            truth.append({"id": "name_typo", "type": "inconsistent_text", "rid": i, "column": "Customer", "clean_value": "Rahul Sharma", "dirty_value": "Rahul Sharmaa", "correct_fix": "review"})
        if i == 15:
            row[2] = "north"
        if i == 16:
            row[2] = "NORTH "
        if i == 17:
            row[0] = "O00001"
            truth.append({"id": "dup_order", "type": "duplicate_id", "rid": i, "column": "Order_ID", "clean_value": oid, "dirty_value": "O00001", "correct_fix": "review"})
        if i == 18:
            row[9] = ""
            truth.append({"id": "blank_status", "type": "missing_value", "rid": i, "column": "Status", "clean_value": "", "dirty_value": "", "correct_fix": "leave"})
        rows.append(row)
    write_csv(ROOT / "sales_messy.csv", headers, rows)
    (ROOT / "sales_messy.truth.json").write_text(json.dumps(truth, indent=2))


def main() -> None:
    students()
    sales()
    print("wrote samples")


if __name__ == "__main__":
    main()
