import struct
from datetime import datetime

from config import PAYMENT_FILE, STATUS_ACTIVE, FREE_NONE_Q
from database import BinaryTable, decode_fixed, encode_fixed

PAYMENT_METHODS = ("Cash", "PromptPay")

# Payment record = 68 bytes
# < i i 20s f 20s i Q
PAYMENT_STRUCT = struct.Struct("<ii20sf20siQ")


def pack_payment(record):
    return PAYMENT_STRUCT.pack(
        record["id"],
        record["order_id"],
        encode_fixed(record["method"], 20),
        float(record["amount"]),
        encode_fixed(record["date"], 20),
        int(record["status"]),
        int(record["next_free"]),
    )


def unpack_payment(raw):
    payment_id, order_id, method, amount, date, status, next_free = (
        PAYMENT_STRUCT.unpack(raw)
    )

    return {
        "id": payment_id,
        "order_id": order_id,
        "method": decode_fixed(method),
        "amount": amount,
        "date": decode_fixed(date),
        "status": status,
        "next_free": next_free,
    }


class PaymentTable(BinaryTable):
    def __init__(self):
        super().__init__(
            PAYMENT_FILE,
            PAYMENT_STRUCT,
            pack_payment,
            unpack_payment,
            initial_id=4001,
        )


def create_payment(order_id, method, amount):
    if method not in PAYMENT_METHODS:
        raise ValueError("Payment method must be Cash or PromptPay.")
    if amount < 0:
        raise ValueError("Amount cannot be negative.")

    return {
        "id": 0,
        "order_id": order_id,
        "method": method,
        "amount": float(amount),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": STATUS_ACTIVE,
        "next_free": FREE_NONE_Q,
    }
