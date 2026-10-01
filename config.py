from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

PRODUCT_FILE = DATA_DIR / "products.dat"
ORDER_FILE = DATA_DIR / "orders.dat"
PAYMENT_FILE = DATA_DIR / "payments.dat"

REPORT_FILE = Path("report.txt")

APP_VERSION = "1.0"
ENCODING = "utf-8"

STATUS_DELETED = 0
STATUS_ACTIVE = 1

FREE_NONE = 0xFFFFFFFF
FREE_NONE_Q = 0xFFFFFFFFFFFFFFFF
