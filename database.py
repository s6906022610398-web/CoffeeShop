import os
import struct
from pathlib import Path

from config import (
    ENCODING,
    FREE_NONE,
    FREE_NONE_Q,
    STATUS_ACTIVE,
    STATUS_DELETED,
)

# Header:
# magic(4) + version(1) + padding(3) +
# record_size(4) + record_count(4) + active_count(4) +
# free_head(4) + next_id(4) = 28 bytes
HEADER_STRUCT = struct.Struct("<4sB3xIIIII")

MAGIC = b"CSDB"
VERSION = 1
HEADER_SIZE = HEADER_STRUCT.size


def encode_fixed(value, size):
    """Encode text to UTF-8, safely truncate, then pad with zero bytes."""
    raw = str(value).encode(ENCODING)

    if len(raw) > size:
        raw = raw[:size]

        # Prevent cutting a UTF-8 character in half
        while True:
            try:
                raw.decode(ENCODING)
                break
            except UnicodeDecodeError:
                raw = raw[:-1]

    return raw.ljust(size, b"\x00")


def decode_fixed(raw):
    """Decode fixed-length UTF-8 bytes."""
    return raw.rstrip(b"\x00").decode(
        ENCODING,
        errors="replace"
    )


class BinaryTable:
    """
    Reusable fixed-length binary table.

    Features:
    - Fixed-length records
    - Binary file I/O
    - Logical delete
    - Free-list
    - In-memory index
    """

    def __init__(
        self,
        path: Path,
        record_struct,
        pack_record,
        unpack_record,
        initial_id=1,
    ):
        self.path = Path(path)
        self.record_struct = record_struct
        self.pack_record = pack_record
        self.unpack_record = unpack_record
        self.initial_id = initial_id
        self.index = {}

        self._ensure_file()
        self.load()

    # ---------------------------------------------------------
    # File initialization
    # ---------------------------------------------------------

    def _ensure_file(self):
        """Create the binary file and header if it does not exist."""

        # Make sure the data folder exists
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Create a new empty file
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.path.touch()

            self._write_header(
                record_count=0,
                active_count=0,
                free_head=FREE_NONE,
                next_id=self.initial_id,
            )

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    def _write_header(
        self,
        record_count,
        active_count,
        free_head,
        next_id,
    ):
        """Write the database header without deleting records."""

        header = HEADER_STRUCT.pack(
            MAGIC,
            VERSION,
            self.record_struct.size,
            record_count,
            active_count,
            free_head,
            next_id,
        )

        # r+b = read/write binary without deleting existing data
        with open(self.path, "r+b") as file:
            file.seek(0)
            file.write(header)
            file.flush()
            os.fsync(file.fileno())

    def _read_header(self):
        """Read and validate the database header."""

        with open(self.path, "rb") as file:
            raw = file.read(HEADER_SIZE)

        if len(raw) != HEADER_SIZE:
            raise ValueError(
                f"{self.path} has an invalid header."
            )

        (
            magic,
            version,
            record_size,
            record_count,
            active_count,
            free_head,
            next_id,
        ) = HEADER_STRUCT.unpack(raw)

        if magic != MAGIC:
            raise ValueError(
                f"{self.path} is not a Coffee Shop data file."
            )

        if version != VERSION:
            raise ValueError(
                f"{self.path} uses an unsupported file version."
            )

        if record_size != self.record_struct.size:
            raise ValueError(
                f"{self.path} record size mismatch: "
                f"file={record_size}, "
                f"expected={self.record_struct.size}"
            )

        return {
            "record_count": record_count,
            "active_count": active_count,
            "free_head": free_head,
            "next_id": next_id,
        }

    # ---------------------------------------------------------
    # Record position
    # ---------------------------------------------------------

    def _offset(self, slot):
        """Calculate byte position of a record slot."""

        return (
            HEADER_SIZE
            + slot * self.record_struct.size
        )

    # ---------------------------------------------------------
    # Read / Write Record
    # ---------------------------------------------------------

    def _read_slot(self, file, slot):
        """Read one fixed-length record."""

        file.seek(self._offset(slot))

        raw = file.read(
            self.record_struct.size
        )

        if len(raw) != self.record_struct.size:
            raise ValueError(
                f"Corrupt record at slot {slot} "
                f"in {self.path}."
            )

        return self.unpack_record(raw)

    def _write_slot(self, file, slot, record):
        """Write one fixed-length record."""

        file.seek(self._offset(slot))

        file.write(
            self.pack_record(record)
        )

    # ---------------------------------------------------------
    # Load
    # ---------------------------------------------------------

    def load(self):
        """Load active records into the in-memory index."""

        header = self._read_header()

        expected_size = (
            HEADER_SIZE
            + (
                header["record_count"]
                * self.record_struct.size
            )
        )

        actual_size = self.path.stat().st_size

        if actual_size != expected_size:
            raise ValueError(
                f"{self.path} size mismatch. "
                f"Expected {expected_size} bytes, "
                f"found {actual_size} bytes."
            )

        self.index.clear()

        with open(self.path, "rb") as file:

            for slot in range(
                header["record_count"]
            ):
                record = self._read_slot(
                    file,
                    slot
                )

                if (
                    record["status"]
                    == STATUS_ACTIVE
                ):
                    self.index[
                        record["id"]
                    ] = slot

        if (
            len(self.index)
            != header["active_count"]
        ):
            raise ValueError(
                f"{self.path} active record "
                f"count does not match its header."
            )

        return header

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get(self, record_id):
        """Get one active record by ID."""

        slot = self.index.get(record_id)

        if slot is None:
            return None

        with open(self.path, "rb") as file:
            return self._read_slot(
                file,
                slot
            )

    # ---------------------------------------------------------
    # Get All Active Records
    # ---------------------------------------------------------

    def all_active(self):
        """Return all active records sorted by ID."""

        records = []

        with open(self.path, "rb") as file:

            for record_id, slot in self.index.items():
                records.append(
                    self._read_slot(
                        file,
                        slot
                    )
                )

        records.sort(
            key=lambda item: item["id"]
        )

        return records

    # ---------------------------------------------------------
    # Add
    # ---------------------------------------------------------

    def add(self, record):
        """
        Add a new record.

        If a deleted slot exists, reuse that slot.
        Otherwise append a new slot at the end.
        """

        header = self._read_header()

        record_id = header["next_id"]

        record["id"] = record_id
        record["status"] = STATUS_ACTIVE

        # -----------------------------------------------------
        # Reuse deleted slot
        # -----------------------------------------------------

        if header["free_head"] != FREE_NONE:

            slot = header["free_head"]

            with open(
                self.path,
                "r+b"
            ) as file:

                old_record = self._read_slot(
                    file,
                    slot
                )

                next_free = old_record[
                    "next_free"
                ]

                record["next_free"] = FREE_NONE_Q

                self._write_slot(
                    file,
                    slot,
                    record
                )

                file.flush()
                os.fsync(file.fileno())

            new_free_head = next_free

            new_record_count = (
                header["record_count"]
            )

        # -----------------------------------------------------
        # Append new slot
        # -----------------------------------------------------

        else:

            slot = header["record_count"]

            record["next_free"] = FREE_NONE_Q

            with open(
                self.path,
                "r+b"
            ) as file:

                self._write_slot(
                    file,
                    slot,
                    record
                )

                file.flush()
                os.fsync(file.fileno())

            new_free_head = FREE_NONE

            new_record_count = (
                header["record_count"] + 1
            )

        # -----------------------------------------------------
        # Update header
        # -----------------------------------------------------

        self._write_header(
            record_count=new_record_count,
            active_count=(
                header["active_count"] + 1
            ),
            free_head=new_free_head,
            next_id=record_id + 1,
        )

        # Update in-memory index
        self.index[record_id] = slot

        return record_id

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(self, record_id, record):
        """Update an existing active record."""

        slot = self.index.get(record_id)

        if slot is None:
            return False

        record["id"] = record_id
        record["status"] = STATUS_ACTIVE
        record["next_free"] = FREE_NONE_Q

        with open(
            self.path,
            "r+b"
        ) as file:

            self._write_slot(
                file,
                slot,
                record
            )

            file.flush()
            os.fsync(file.fileno())

        return True

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(self, record_id):
        """
        Logical delete.

        The record remains inside the binary file,
        but its status becomes DELETED and its slot
        is added to the free-list.
        """

        slot = self.index.get(record_id)

        if slot is None:
            return False

        header = self._read_header()

        with open(
            self.path,
            "r+b"
        ) as file:

            old_record = self._read_slot(
                file,
                slot
            )

            old_record["status"] = STATUS_DELETED

            # Link this deleted slot to the
            # previous free-list head
            old_record["next_free"] = (
                header["free_head"]
            )

            self._write_slot(
                file,
                slot,
                old_record
            )

            file.flush()
            os.fsync(file.fileno())

        # Update header
        self._write_header(
            record_count=header["record_count"],
            active_count=(
                header["active_count"] - 1
            ),
            free_head=slot,
            next_id=header["next_id"],
        )

        # Remove from active index
        del self.index[record_id]

        return True

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def stats(self):
        """Return database statistics."""

        header = self._read_header()

        deleted = (
            header["record_count"]
            - header["active_count"]
        )

        return {
            "active": header["active_count"],
            "deleted": deleted,
            "free_slots": deleted,
            "total_slots": header["record_count"],
        }