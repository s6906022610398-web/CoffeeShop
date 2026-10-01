import struct
from datetime import datetime

from config import ORDER_FILE, STATUS_ACTIVE, FREE_NONE_Q
from database import BinaryTable, decode_fixed, encode_fixed

# Order record = 68 bytes
# < id, customer_id, product_id_1, qty_1, product_id_2, qty_2, product_id_3, qty_3, total, date, status, next_free
ORDER_STRUCT = struct.Struct("<iiiiiiiif20siQ")


def pack_order(record):
    items = record.get("items", [])
    items = (items + [(0, 0)] * 3)[:3]

    return ORDER_STRUCT.pack(
        record["id"],
        record["customer_id"],
        items[0][0], items[0][1],
        items[1][0], items[1][1],
        items[2][0], items[2][1],
        float(record["total"]),
        encode_fixed(record["date"], 20),
        int(record["status"]),
        int(record["next_free"]),
    )


def unpack_order(raw):
    (
        record_id, customer_id,
        p1, q1, p2, q2, p3, q3,
        total, date, status, next_free,
    ) = ORDER_STRUCT.unpack(raw)

    items = [(p1, q1), (p2, q2), (p3, q3)]
    items = [(pid, qty) for pid, qty in items if pid > 0 and qty > 0]

    return {
        "id": record_id,
        "customer_id": customer_id,
        "product_id": items[0][0] if items else 0,
        "quantity": items[0][1] if items else 0,
        "items": items,
        "total": total,
        "date": decode_fixed(date),
        "status": status,
        "next_free": next_free,
    }


class OrderTable(BinaryTable):
    def __init__(self):
        super().__init__(
            ORDER_FILE,
            ORDER_STRUCT,
            pack_order,
            unpack_order,
            initial_id=3001,
        )


def create_order(customer_id, items, total):
    if customer_id <= 0:
        raise ValueError("Customer ID must be greater than 0.")
    if not items:
        raise ValueError("Order must contain at least one product.")
    if len(items) > 3:
        raise ValueError("An order can contain up to 3 different products.")
    if total < 0:
        raise ValueError("Total cannot be negative.")

    cleaned = []
    for product_id, quantity in items:
        if product_id <= 0:
            raise ValueError("Product ID must be greater than 0.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")
        cleaned.append((int(product_id), int(quantity)))

    return {
        "id": 0,
        "customer_id": int(customer_id),
        "product_id": cleaned[0][0],
        "quantity": cleaned[0][1],
        "items": cleaned,
        "total": float(total),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": STATUS_ACTIVE,
        "next_free": FREE_NONE_Q,
    }
