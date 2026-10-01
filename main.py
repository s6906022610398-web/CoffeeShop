from datetime import datetime

from order import OrderTable, create_order
from payment import PAYMENT_METHODS, PaymentTable, create_payment
from product import ProductTable, create_product
from report import (
    generate_product_report,
    generate_order_report,
    generate_payment_report,
)


def read_int(prompt, minimum=None):
    while True:
        try:
            value = int(input(prompt).strip())

            if minimum is not None and value < minimum:
                print(f"Please enter a number >= {minimum}.")
                continue

            return value
        except ValueError:
            print("Please enter a valid integer.")


def read_float(prompt, minimum=None):
    while True:
        try:
            value = float(input(prompt).strip())

            if minimum is not None and value < minimum:
                print(f"Please enter a number >= {minimum}.")
                continue

            return value
        except ValueError:
            print("Please enter a valid number.")


def read_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def choose_payment_method():
    print("1. Cash")
    print("2. PromptPay")

    while True:
        choice = input("Choose method: ").strip()

        if choice == "1":
            return "Cash"
        if choice == "2":
            return "PromptPay"

        print("Invalid choice. Please select 1 or 2.")


def print_products(products):
    rows = products.all_active()

    if not rows:
        print("\nNo products found.")
        return

    print("\n" + "-" * 90)
    print(
        f"{'ID':<8}"
        f"{'Name':<25}"
        f"{'Category':<17}"
        f"{'Price':>10}"
        f"{'Status':>12}"
    )
    print("-" * 90)

    for row in rows:
        status = "Active" if row["status"] == 1 else "Deleted"

        print(
            f"{row['id']:<8}"
            f"{row['name']:<25}"
            f"{row['category']:<17}"
            f"{row['price']:>10.2f}"
            f"{status:>12}"
        )

    print("-" * 90)


def format_order_items(row):
    return ", ".join(
        f"{product_id}x{quantity}"
        for product_id, quantity in row.get("items", [])
    )


def print_orders(orders):
    rows = orders.all_active()

    if not rows:
        print("\nNo orders found.")
        return

    print("\n" + "-" * 110)
    print(
        f"{'ID':<8}"
        f"{'Customer':<12}"
        f"{'Products':<28}"
        f"{'Total':<14}"
        f"{'Date':<20}"
        f"{'Status':>10}"
    )
    print("-" * 110)

    for row in rows:
        status = "Active" if row["status"] == 1 else "Deleted"
        print(
            f"{row['id']:<8}"
            f"{row['customer_id']:<12}"
            f"{format_order_items(row):<28}"
            f"{row['total']:<14.2f}"
            f"{row['date']:<20}"
            f"{status:>10}"
        )

    print("-" * 110)


def print_payments(payments):
    rows = payments.all_active()

    if not rows:
        print("\nNo payments found.")
        return

    print("\n" + "-" * 105)
    print(
        f"{'ID':<10}"
        f"{'Order':<10}"
        f"{'Method':<12}"
        f"{'Amount':<14}"
        f"{'Date':<20}"
        f"{'Status':>10}"
    )
    print("-" * 105)

    for row in rows:
        status = "Paid" if row["status"] == 1 else "Deleted"

        print(
            f"{row['id']:<10}"
            f"{row['order_id']:<10}"
            f"{row['method']:<12}"
            f"{row['amount']:<14.2f}"
            f"{row['date']:<20}"
            f"{status:>10}"
        )

    print("-" * 105)

def add_product(products, activities):
    print("\n--- Add Product ---")
    name = read_text("Name: ")
    category = read_text("Category: ")
    price = read_float("Price (THB): ", 0)

    try:
        record_id = products.add(create_product(name, category, price))
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ADD",
            "Product",
            record_id,
        ))
        print(f"Product added successfully. ID = {record_id}")
    except ValueError as exc:
        print(f"Error: {exc}")


def add_order(products, orders, payments, activities):
    print("\n--- Add Order ---")
    customer_id = read_int("Customer ID: ", 1)
    items = []
    total = 0.0

    while len(items) < 3:
        print_products(products)
        product_id = read_int("Product ID: ", 1)
        product = products.get(product_id)

        if product is None:
            print("Product ID not found.")
            continue

        quantity = read_int("Quantity: ", 1)

        # If the same product is selected again, combine the quantity.
        found = False
        for index, (pid, qty) in enumerate(items):
            if pid == product_id:
                items[index] = (pid, qty + quantity)
                found = True
                break

        if not found:
            items.append((product_id, quantity))

        total = sum(products.get(pid)["price"] * qty for pid, qty in items)
        print(f"Current Total = {total:.2f} THB")

        if len(items) == 3:
            print("Maximum 3 different products per order.")
            break

        more = input("Add another product? (Y/N): ").strip().upper()
        if more != "Y":
            break

    print("\nOrder Summary")
    for product_id, quantity in items:
        product = products.get(product_id)
        print(f"- {product['name']} x{quantity}")
    print(f"Total = {total:.2f} THB")

    try:
        record_id = orders.add(create_order(customer_id, items, total))

        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ADD",
            "Order",
            record_id,
        ))

        print(f"Order added successfully. ID = {record_id}")

        pay_now = input("Pay now? (Y/N): ").strip().upper()
        if pay_now == "Y":
            add_payment_for_order(record_id, total, payments, activities)

    except ValueError as exc:
        print(f"Error: {exc}")


def add_payment_for_order(order_id, amount, payments, activities):
    print("\n--- Payment ---")
    print(f"Order ID: {order_id}")
    print(f"Amount = {amount:.2f} THB")
    method = choose_payment_method()

    try:
        record_id = payments.add(create_payment(order_id, method, amount))
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ADD",
            "Payment",
            record_id,
        ))
        print(f"Payment added successfully. ID = {record_id}")
    except ValueError as exc:
        print(f"Error: {exc}")


def add_payment(orders, payments, activities):
    print("\n--- Add Payment ---")
    print_orders(orders)

    order_id = read_int("Order ID: ", 1)
    order = orders.get(order_id)

    if order is None:
        print("Order ID not found.")
        return

    print(f"Amount = {order['total']:.2f} THB")
    method = choose_payment_method()

    try:
        record_id = payments.add(
            create_payment(order_id, method, order["total"])
        )
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ADD",
            "Payment",
            record_id,
        ))
        print(f"Payment added successfully. ID = {record_id}")
    except ValueError as exc:
        print(f"Error: {exc}")


def update_product(products, activities):
    print("\n--- Update Product ---")
    print_products(products)

    record_id = read_int("Product ID: ", 1)
    old = products.get(record_id)

    if old is None:
        print("Product ID not found.")
        return

    name = read_text(f"Name [{old['name']}]: ")
    category = read_text(f"Category [{old['category']}]: ")
    price = read_float(f"Price [{old['price']:.2f}]: ", 0)

    updated = create_product(name, category, price)
    products.update(record_id, updated)

    activities.append((
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "UPDATE",
        "Product",
        record_id,
    ))
    print("Product updated successfully.")


def update_order(products, orders, activities):
    print("\n--- Update Order ---")
    print_orders(orders)

    record_id = read_int("Order ID: ", 1)
    old = orders.get(record_id)

    if old is None:
        print("Order ID not found.")
        return

    customer_id = read_int(f"Customer ID [{old['customer_id']}]: ", 1)
    items = []

    while len(items) < 3:
        print_products(products)
        product_id = read_int("Product ID: ", 1)
        product = products.get(product_id)
        if product is None:
            print("Product ID not found.")
            continue

        quantity = read_int("Quantity: ", 1)
        items.append((product_id, quantity))

        if len(items) == 3:
            break
        more = input("Add another product? (Y/N): ").strip().upper()
        if more != "Y":
            break

    total = sum(products.get(pid)["price"] * qty for pid, qty in items)
    updated = create_order(customer_id, items, total)
    updated["date"] = old["date"]
    orders.update(record_id, updated)

    activities.append((
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "UPDATE",
        "Order",
        record_id,
    ))
    print("Order updated successfully.")


def update_payment(orders, payments, activities):
    print("\n--- Update Payment ---")
    print_payments(payments)

    record_id = read_int("Payment ID: ", 1)
    old = payments.get(record_id)

    if old is None:
        print("Payment ID not found.")
        return

    order = orders.get(old["order_id"])
    if order is None:
        print("Related order no longer exists.")
        return

    print(f"Order ID: {old['order_id']}")
    print(f"Amount: {order['total']:.2f} THB")
    method = choose_payment_method()

    updated = create_payment(
        old["order_id"],
        method,
        order["total"],
    )
    updated["date"] = old["date"]
    payments.update(record_id, updated)

    activities.append((
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "UPDATE",
        "Payment",
        record_id,
    ))
    print("Payment updated successfully.")


def delete_product(products, orders, activities):
    print("\n--- Delete Product ---")
    print_products(products)

    record_id = read_int("Product ID: ", 1)

    for order in orders.all_active():
        if any(pid == record_id for pid, qty in order.get("items", [])):
            print("Cannot delete: this product is used by an active order.")
            return

    if products.delete(record_id):
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DELETE",
            "Product",
            record_id,
        ))
        print("Product deleted successfully.")
    else:
        print("Product ID not found.")


def delete_order(orders, payments, activities):
    print("\n--- Delete Order ---")
    print_orders(orders)

    record_id = read_int("Order ID: ", 1)

    # Delete related payments first, so the order can be removed
    # without leaving orphan payment records.
    related_payments = [
        payment["id"]
        for payment in payments.all_active()
        if payment["order_id"] == record_id
    ]

    for payment_id in related_payments:
        payments.delete(payment_id)
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DELETE",
            "Payment",
            payment_id,
        ))

    if orders.delete(record_id):
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DELETE",
            "Order",
            record_id,
        ))
        print("Order deleted successfully.")
    else:
        print("Order ID not found.")


def delete_payment(payments, activities):
    print("\n--- Delete Payment ---")
    print_payments(payments)

    record_id = read_int("Payment ID: ", 1)

    if payments.delete(record_id):
        activities.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DELETE",
            "Payment",
            record_id,
        ))
        print("Payment deleted successfully.")
    else:
        print("Payment ID not found.")


def add_menu(products, orders, payments, activities):
    while True:
        print("\n=== Add Menu ===")
        print("1. Product")
        print("2. Order")
        print("3. Payment")
        print("0. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            add_product(products, activities)
        elif choice == "2":
            add_order(products, orders, payments, activities)
        elif choice == "3":
            add_payment(orders, payments, activities)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def update_menu(products, orders, payments, activities):
    while True:
        print("\n=== Update Menu ===")
        print("1. Product")
        print("2. Order")
        print("3. Payment")
        print("0. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            update_product(products, activities)
        elif choice == "2":
            update_order(products, orders, activities)
        elif choice == "3":
            update_payment(orders, payments, activities)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def delete_menu(products, orders, payments, activities):
    while True:
        print("\n=== Delete Menu ===")
        print("1. Product")
        print("2. Order")
        print("3. Payment")
        print("0. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            delete_product(products, orders, activities)
        elif choice == "2":
            delete_order(orders, payments, activities)
        elif choice == "3":
            delete_payment(payments, activities)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def view_menu(products, orders, payments):
    while True:
        print("\n=== View Menu ===")
        print("1. Products")
        print("2. Orders")
        print("3. Payments")
        print("0. Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            print_products(products)
        elif choice == "2":
            print_orders(orders)
        elif choice == "3":
            print_payments(payments)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def main():
    try:
        products = ProductTable()
        orders = OrderTable()
        payments = PaymentTable()
    except ValueError as exc:
        print("\nDATA FILE ERROR")
        print(exc)
        print("Check the .dat files before running the program again.")
        return

    activities = []

    while True:
        print("\n" + "=" * 50)
        print("       COFFEE SHOP MANAGEMENT SYSTEM")
        print("=" * 50)
        print("1. Add")
        print("2. Update")
        print("3. Delete")
        print("4. View")
        print("5. Generate Report")
        print("0. Exit")
        print("=" * 50)

        choice = input("Choose: ").strip()

        if choice == "1":
            add_menu(products, orders, payments, activities)

        elif choice == "2":
            update_menu(products, orders, payments, activities)

        elif choice == "3":
            delete_menu(products, orders, payments, activities)

        elif choice == "4":
            view_menu(products, orders, payments)

        elif choice == "5":
            while True:
                print("\n=== Generate Report ===")
                print("1. Product Report")
                print("2. Order Report")
                print("3. Payment Report")
                print("0. Back")

                report_choice = input("Choose: ").strip()

                if report_choice == "1":
                    path = generate_product_report(products)
                    print(f"Report generated: {path}")

                elif report_choice == "2":
                    path = generate_order_report(products, orders)
                    print(f"Report generated: {path}")

                elif report_choice == "3":
                    path = generate_payment_report(payments)
                    print(f"Report generated: {path}")

                elif report_choice == "0":
                    break

                else:
                    print("Invalid choice.")

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("Invalid choice. Please select 0-5.")


if __name__ == "__main__":
    main()
