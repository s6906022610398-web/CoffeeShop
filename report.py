from datetime import datetime
from pathlib import Path

from config import APP_VERSION, REPORT_FILE

REPORT_DIR = Path(REPORT_FILE).parent / "reports"
PRODUCT_REPORT_FILE = REPORT_DIR / "product_report.txt"
ORDER_REPORT_FILE = REPORT_DIR / "order_report.txt"
PAYMENT_REPORT_FILE = REPORT_DIR / "payment_report.txt"


def line(char="-", width=90):
    return char * width


def status_text(status):
    return "Active" if status == 1 else "Deleted"


def payment_status_text(status):
    return "Paid" if status == 1 else "Deleted"


def _header(title, data_files):
    return [
        "=" * 90,
        f"                 {title}",
        "=" * 90,
        f"Generated At : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"App Version  : {APP_VERSION}",
        "Endianness   : Little-Endian",
        "Encoding     : UTF-8 (Fixed-length Record)",
        f"Data Files   : {data_files}",
        "=" * 90,
        "",
    ]


def generate_product_report(products):
    rows = products.all_active()
    stats = products.stats()
    lines = _header(
        "Coffee Shop Management System - Product Report",
        "products.dat",
    )
    lines += [
        "=== Product Report ===",
        line(),
        "| ID     | Name                     | Category       | Price (THB) | Status  |",
        line(),
    ]
    for row in rows:
        lines.append(
            f"| {row['id']:<6} | {row['name']:<24} | {row['category']:<14} | "
            f"{row['price']:>11.2f} | {status_text(row['status']):<7} |"
        )
    if not rows:
        lines.append("| No active products.                                                               |")
    lines += [
        line(),
        "",
        "=== Product Summary ===",
        line("-"),
        f"Active Products : {stats['active']}",
        f"Deleted Products: {stats['deleted']}",
        f"Free Slots      : {stats['free_slots']}",
        "",
        "=" * 90,
        "                              End of Product Report",
        "=" * 90,
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PRODUCT_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return PRODUCT_REPORT_FILE


def generate_order_report(products, orders):
    rows = orders.all_active()
    product_map = {row["id"]: row for row in products.all_active()}
    stats = orders.stats()
    total_sales = sum(row["total"] for row in rows)
    lines = _header(
        "Coffee Shop Management System - Order Report",
        "products.dat, orders.dat",
    )
    lines += [
        "=== Order Report ===",
        "-" * 105,
        "| Order ID | Customer | Products                          | Total (THB) | Date                | Status  |",
        "-" * 105,
    ]
    for row in rows:
        product_text = ", ".join(
            f"{product_map.get(pid, {'name': str(pid)})['name']} x{qty}"
            for pid, qty in row.get("items", [])
        )
        lines.append(
            f"| {row['id']:<8} | {row['customer_id']:<8} | {product_text:<33} | "
            f"{row['total']:>10.2f} | {row['date']:<19} | "
            f"{status_text(row['status']):<7} |"
        )
    if not rows:
        lines.append(
            "| No active orders.                                                                                               |"
        )
    lines += [
        "-" * 105,
        "",
        "=== Customer Order Summary ===",
        "-" * 90,
        "Customer ID    Total Cups    Products Ordered",
    ]
    customer_summary = {}
    for row in rows:
        customer_id = row["customer_id"]
        customer_summary.setdefault(customer_id, {"cups": 0, "products": []})
        for pid, qty in row.get("items", []):
            customer_summary[customer_id]["cups"] += qty
            name = product_map.get(pid, {"name": str(pid)})["name"]
            customer_summary[customer_id]["products"].append(f"{name} x{qty}")
    if customer_summary:
        for customer_id, data in sorted(customer_summary.items()):
            lines.append(
                f"{customer_id:<14} {data['cups']:<12} {', '.join(data['products'])}"
            )
    else:
        lines.append("No active customer orders.")
    lines += [
        "",
        "=== Order Summary ===",
        line("-"),
        f"Active Orders : {stats['active']}",
        f"Deleted Orders: {stats['deleted']}",
        f"Free Slots    : {stats['free_slots']}",
        f"Total Sales   : {total_sales:.2f} THB",
        "",
        "=" * 90,
        "                              End of Order Report",
        "=" * 90,
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ORDER_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ORDER_REPORT_FILE


def generate_payment_report(payments):
    rows = payments.all_active()
    stats = payments.stats()
    cash_count = sum(row["method"] == "Cash" for row in rows)
    promptpay_count = sum(row["method"] == "PromptPay" for row in rows)
    total_paid = sum(row["amount"] for row in rows)
    lines = _header(
        "Coffee Shop Management System - Payment Report",
        "payments.dat",
    )
    lines += [
        "=== Payment Report ===",
        "-" * 95,
        "| Payment ID | Order ID | Method    | Amount (THB) | Date                | Status  |",
        "-" * 95,
    ]
    for row in rows:
        lines.append(
            f"| {row['id']:<10} | {row['order_id']:<8} | {row['method']:<9} | "
            f"{row['amount']:>12.2f} | {row['date']:<19} | "
            f"{payment_status_text(row['status']):<7} |"
        )
    if not rows:
        lines.append("| No active payments.                                                                       |")
    lines += [
        "-" * 95,
        "",
        "=== Payment Summary ===",
        line("-"),
        f"Cash Payments      : {cash_count}",
        f"PromptPay Payments : {promptpay_count}",
        f"Total Paid         : {total_paid:.2f} THB",
        f"Active Payments    : {stats['active']}",
        f"Deleted Payments   : {stats['deleted']}",
        f"Free Slots         : {stats['free_slots']}",
        "",
        "=" * 90,
        "                            End of Payment Report",
        "=" * 90,
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PAYMENT_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return PAYMENT_REPORT_FILE
