import struct

from config import PRODUCT_FILE, STATUS_ACTIVE, STATUS_DELETED, FREE_NONE_Q
from database import BinaryTable, decode_fixed, encode_fixed

# Product record = 80 bytes
# < i 40s 20s f i Q
PRODUCT_STRUCT = struct.Struct("<i40s20sfiQ")


def pack_product(record):
    return PRODUCT_STRUCT.pack(
        record["id"],
        encode_fixed(record["name"], 40),
        encode_fixed(record["category"], 20),
        float(record["price"]),
        int(record["status"]),
        int(record["next_free"]),
    )


def unpack_product(raw):
    record_id, name, category, price, status, next_free = PRODUCT_STRUCT.unpack(raw)

    return {
        "id": record_id,
        "name": decode_fixed(name),
        "category": decode_fixed(category),
        "price": price,
        "status": status,
        "next_free": next_free,
    }


class ProductTable(BinaryTable):
    def __init__(self):
        super().__init__(
            PRODUCT_FILE,
            PRODUCT_STRUCT,
            pack_product,
            unpack_product,
            initial_id=2001,
        )


def create_product(name, category, price):
    if not name.strip():
        raise ValueError("Product name cannot be empty.")
    if not category.strip():
        raise ValueError("Category cannot be empty.")
    if price < 0:
        raise ValueError("Price cannot be negative.")

    return {
        "id": 0,
        "name": name.strip(),
        "category": category.strip(),
        "price": float(price),
        "status": STATUS_ACTIVE,
        "next_free": FREE_NONE_Q,
    }
