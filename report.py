from datetime import datetime

from config import APP_VERSION, REPORT_FILE


def line(char="-", width=90):
    return char * width


def status_text(status):
    return "Active" if status == 1 else "Deleted"


def payment_status_text(status):
    return "Paid" if status == 1 else "Deleted"


def generate_report(products, orders, payments, activities):
    product_rows = products.all_active()
    order_rows = orders.all_active()
    payment_rows = payments.all_active()

    product_map = {row["id"]: row for row in product_rows}
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
        "=== 1. Products ===",
        line(),
        "| ID     | Name                     | Category       | Price (THB) | Status  |",
        line(),
    ]

    for row in product_rows:
        lines.append(
            f"| {row['id']:<6} | {row['name']:<24} | {row['category']:<14} | "
            f"{row['price']:>11.2f} | {status_text(row['status']):<7} |"
        )
    if not product_rows:
        lines.append("| No active products.                                                               |")

    lines += [
        line(), "",
        "=== 2. Orders ===",
        "-" * 105,
        "| Order ID | Customer | Products                          | Total (THB) | Date                | Status  |",
        "-" * 105,
    ]

    for row in order_rows:
        product_text = ", ".join(
            f"{product_map.get(pid, {'name': str(pid)})['name']} x{qty}"
            for pid, qty in row.get("items", [])
        )
        lines.append(
            f"| {row['id']:<8} | {row['customer_id']:<8} | {product_text:<33} | "
            f"{row['total']:>10.2f} | {row['date']:<19} | {status_text(row['status']):<7} |"
        )
    if not order_rows:
        lines.append("| No active orders.                                                                                               |")

    lines += [
        "-" * 105, "",
        "=== 3. Payments ===",
        "-" * 95,
        "| Payment ID | Order ID | Method    | Amount (THB) | Date                | Status  |",
        "-" * 95,
    ]

    for row in payment_rows:
        lines.append(
            f"| {row['id']:<10} | {row['order_id']:<8} | {row['method']:<9} | "
            f"{row['amount']:>12.2f} | {row['date']:<19} | {payment_status_text(row['status']):<7} |"
        )
    if not payment_rows:
        lines.append("| No active payments.                                                                       |")

    lines += [
        "-" * 95, "",
        "=== 4. Database Summary ===",
        "-" * 32,
        f"Products - Active: {product_stats['active']} | Deleted: {product_stats['deleted']} | Free Slots: {product_stats['free_slots']}",
        f"Orders   - Active: {order_stats['active']} | Deleted: {order_stats['deleted']} | Free Slots: {order_stats['free_slots']}",
        f"Payments - Active: {payment_stats['active']} | Deleted: {payment_stats['deleted']} | Free Slots: {payment_stats['free_slots']}",
        f"Total Sales : {total_sales:.2f} THB",
        "",
        "=== 5. Payment Summary ===",
        "-" * 32,
        f"Cash       : {cash_count}",
        f"PromptPay  : {promptpay_count}",
        "",
        "=== 6. Customer Order Summary ===",
        "-" * 90,
        "Customer ID    Total Cups    Products Ordered",
    ]

    customer_summary = {}
    for row in order_rows:
        customer_id = row["customer_id"]
        if customer_id not in customer_summary:
            customer_summary[customer_id] = {"cups": 0, "products": []}
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
        "=== 7. Recent Activity ===",
        "-" * 32,
    ]
    recent = activities[-10:]
    if recent:
        for timestamp, action, entity, record_id in recent:
            lines.append(f"{timestamp} | {action:<6} | {entity} ID {record_id}")
    else:
        lines.append("No activity in the current session.")

    lines += ["", "=" * 90, "                              End of Report", "=" * 90]
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_FILE
