from datetime import datetime

from config import APP_VERSION, REPORT_FILE


def line(char="-", width=90):
    return char * width


def status_text(status):
    return "Active" if status == 1 else "Deleted"


def generate_report(products, orders, payments, activities):
    product_rows = products.all_active()
    order_rows = orders.all_active()
    payment_rows = payments.all_active()

    total_sales = sum(row["total"] for row in order_rows)
    cash_count = sum(row["method"] == "Cash" for row in payment_rows)
    promptpay_count = sum(row["method"] == "PromptPay" for row in payment_rows)

    product_stats = products.stats()
    order_stats = orders.stats()
    payment_stats = payments.stats()

    lines = [
        "=" * 90,
        "                 Coffee Shop Management System - Summary Report",
        "=" * 90,
        f"Generated At : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"App Version  : {APP_VERSION}",
        "Endianness   : Little-Endian",
        "Encoding     : UTF-8 (Fixed-length Record)",
        "Data Files   : products.dat, orders.dat, payments.dat",
        "=" * 90,
        "",
        "=== 1. สินค้าทั้งหมด (Products) ===",
        line(),
        "| ID     | Name                     | Category       | Price (THB) | Status  |",
        line(),
    ]

    for row in product_rows:
        lines.append(
            f"| {row['id']:<6} | {row['name']:<24} | "
            f"{row['category']:<14} | {row['price']:>11.2f} | "
            f"{status_text(row['status']):<7} |"
        )

    if not product_rows:
        lines.append("| No active products.                                                               |")

    lines += [
        line(),
        "",
        "=== 2. สรุปคำสั่งซื้อ (Orders) ===",
        "-" * 95,
        "| Order ID | Product ID | Quantity | Total (THB) | Date                | Status  |",
        "-" * 95,
    ]

    for row in order_rows:
        lines.append(
            f"| {row['id']:<8} | {row['product_id']:<10} | "
            f"{row['quantity']:<8} | {row['total']:>11.2f} | "
            f"{row['date']:<19} | {status_text(row['status']):<7} |"
        )

    if not order_rows:
        lines.append("| No active orders.                                                                          |")

    lines += [
        "-" * 95,
        "",
        "=== 3. การชำระเงิน (Payments) ===",
        "-" * 95,
        "| Payment ID | Order ID | Method    | Amount (THB) | Date                | Status  |",
        "-" * 95,
    ]

    for row in payment_rows:
        lines.append(
            f"| {row['id']:<10} | {row['order_id']:<8} | "
            f"{row['method']:<9} | {row['amount']:>12.2f} | "
            f"{row['date']:<19} | {status_text(row['status']):<7} |"
        )

    if not payment_rows:
        lines.append("| No active payments.                                                                       |")

    lines += [
        "-" * 95,
        "",
        "=== 4. Database Summary ===",
        "-" * 32,
        "Products",
        f"- Active     : {product_stats['active']}",
        f"- Deleted    : {product_stats['deleted']}",
        f"- Free Slots : {product_stats['free_slots']}",
        "",
        "Orders",
        f"- Active     : {order_stats['active']}",
        f"- Deleted    : {order_stats['deleted']}",
        f"- Free Slots : {order_stats['free_slots']}",
        "",
        "Payments",
        f"- Active     : {payment_stats['active']}",
        f"- Deleted    : {payment_stats['deleted']}",
        f"- Free Slots : {payment_stats['free_slots']}",
        "",
        f"Total Sales : {total_sales:.2f} THB",
        "",
        "=== 5. Payment Summary ===",
        "-" * 32,
        f"Cash       : {cash_count}",
        f"PromptPay  : {promptpay_count}",
        "",
        "=== 6. Recent Activity ===",
        "-" * 32,
    ]

    recent = activities[-10:]
    if recent:
        for timestamp, action, entity, record_id in recent:
            lines.append(
                f"{timestamp} | {action:<6} | {entity} ID {record_id}"
            )
    else:
        lines.append("No activity in the current session.")

    lines += [
        "",
        "=" * 90,
        "                              End of Report",
        "=" * 90,
    ]

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_FILE
