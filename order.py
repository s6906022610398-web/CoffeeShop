import struct
from datetime import datetime

from config import ORDER_FILE, STATUS_ACTIVE, FREE_NONE_Q
from database import BinaryTable, decode_fixed, encode_fixed

# Order record = 48 bytes
# < i i i f 20s i Q
ORDER_STRUCT = struct.Struct("<iiif20siQ")


def pack_order(record):
    return ORDER_STRUCT.pack(
        record["id"],
        record["product_id"],
        int(record["quantity"]),
        float(record["total"]),
        encode_fixed(record["date"], 20),
        int(record["status"]),
        int(record["next_free"]),
    )


def unpack_order(raw):
    record_id, product_id, quantity, total, date, status, next_free = (
        ORDER_STRUCT.unpack(raw)
    )

    return {
        "id": record_id,
        "product_id": product_id,
        "quantity": quantity,
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


def create_order(product_id, quantity, total):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    if total < 0:
        raise ValueError("Total cannot be negative.")

    return {
        "id": 0,
        "product_id": product_id,
        "quantity": int(quantity),
        "total": float(total),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": STATUS_ACTIVE,
        "next_free": FREE_NONE_Q,
    }
