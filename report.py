from datetime import datetime

from config import APP_VERSION, REPORT_FILE


def line(char="-", width=100):
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

    customer_summary = {}

    for order in order_rows:
        customer_id = order["customer_id"]

        if customer_id not in customer_summary:
            customer_summary[customer_id] = {
                "total_cups": 0,
                "products": {},
            }

        customer_summary[customer_id]["total_cups"] += order["quantity"]

        product = products.get(order["product_id"])
        product_name = (
            product["name"]
            if product is not None
            else f"Product {order['product_id']}"
        )

        customer_summary[customer_id]["products"][product_name] = (
            customer_summary[customer_id]["products"].get(product_name, 0)
            + order["quantity"]
        )

    lines = [
        "=" * 100,
        "                         Coffee Shop Management System - Summary Report",
        "=" * 100,
        f"Generated At : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"App Version  : {APP_VERSION}",
        "Endianness   : Little-Endian",
        "Encoding     : UTF-8 (Fixed-length Record)",
        "Data Files   : products.dat, orders.dat, payments.dat",
        "=" * 100,
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
        "-" * 105,
        "| Order ID | Customer ID | Product ID | Quantity | Total (THB) | Date                | Status  |",
        "-" * 105,
    ]

    for row in order_rows:
        lines.append(
            f"| {row['id']:<8} | {row['customer_id']:<11} | "
            f"{row['product_id']:<10} | {row['quantity']:<8} | "
            f"{row['total']:>11.2f} | {row['date']:<19} | "
            f"{status_text(row['status']):<7} |"
        )

    if not order_rows:
        lines.append("| No active orders.                                                                                         |")

    lines += [
        "-" * 105,
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
        "=== 6. Customer Order Summary ===",
        "-" * 95,
        "| Customer ID | Total Cups | Products Ordered",
        "-" * 95,
    ]

    if customer_summary:
        for customer_id in sorted(customer_summary):
            summary = customer_summary[customer_id]
            product_text = ", ".join(
                f"{name} x{qty}"
                for name, qty in summary["products"].items()
            )
            lines.append(
                f"| {customer_id:<11} | {summary['total_cups']:<10} | {product_text}"
            )
    else:
        lines.append("| No customer orders. |")

    lines += [
        "-" * 95,
        f"Total Customers : {len(customer_summary)}",
        f"Total Cups      : {sum(item['total_cups'] for item in customer_summary.values())}",
        "",
        "=== 7. Recent Activity ===",
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
        "=" * 100,
        "                                  End of Report",
        "=" * 100,
    ]

    REPORT_FILE.write_text("
".join(lines) + "
", encoding="utf-8")
    return REPORT_FILE
