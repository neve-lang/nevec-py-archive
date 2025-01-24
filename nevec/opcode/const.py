import struct

from typing import Self, List, Tuple
from enum import auto, Enum

class ValType(Enum):
    NUM = auto()
    BOOL = auto()
    NIL = auto() 
    OBJ = auto()

    EMPTY = auto()


class ObjType(Enum):
    STR = auto()
    TABLE = auto()


class Const[T]:
    def __init__(self, value: T, id=-1):
        self.value = value
        self.id: int = id
        
    def emit_int(self, data: int, size: int) -> bytes:
        return data.to_bytes(size, byteorder="little")

    def emit_type(self, type: ValType | ObjType) -> bytes:
        return self.emit_int(type.value - 1, 1)

    def emit(self) -> List[bytes]:
        ...

    def __eq__(self, other: Self) -> bool:
        _ = other

        ...


class BoolLit(Const[bool]):
    def emit(self) -> List[bytes]:
        return [
            self.emit_type(ValType.BOOL),
            self.emit_int(int(self.value), 1)
        ]

    def __eq__(self, other: Const) -> bool:
        return (
            isinstance(other, BoolLit) and
            self.value == other.value
        )

    def __repr__(self) -> str:
        return str(self.value).lower()


class NilLit(Const[None]):
    def emit(self) -> List[bytes]:
        return [
            self.emit_type(ValType.NIL)
        ]

    def __eq__(self, other: Const) -> bool:
        return isinstance(other, NilLit)

    def __repr__(self) -> str:
        return "nil"


class Empty(Const[None]):
    def emit(self) -> List[bytes]:
        return [
            self.emit_type(ValType.EMPTY)
        ]

    def __eq__(self, other: Const) -> bool:
        return isinstance(other, Empty)

    def __repr__(self) -> str:
        return "()"


class Num(Const[float]):
    def emit(self) -> List[bytes]:
        return [
            self.emit_type(ValType.NUM),
            struct.pack("<d", self.value)
        ]

    def __eq__(self, other: Const) -> bool:
        return (
            isinstance(other, Num) and
            self.value == other.value
        )

    def __repr__(self) -> str:
        return str(self.value)


class StrLit(Const[Tuple[str, bool]]):
    def emit(self) -> List[bytes]:
        string = self.value[0]
        is_interned = int(self.value[1])

        return [
            self.emit_type(ValType.OBJ),
            self.emit_type(ObjType.STR),
            self.emit_int(len(string), 4),
            string.encode(),
            self.emit_int(is_interned, 1) 
        ]

    def __eq__(self, other: Const) -> bool:
        return (
            isinstance(other, StrLit) and
            self.value == other.value
        )

    def __repr__(self) -> str:
        return self.value[0]


class TableLit(Const[List[Const]]):
    def emit(self) -> List[bytes]:
        entries = [e.emit() for e in self.value]
        entries = [e for e in entries if not isinstance(e, bytes)]

        assert all(isinstance(e, list) for e in entries)

        emission: List[bytes] = [b for e in entries for b in e]

        return [
            self.emit_type(ValType.OBJ),
            self.emit_type(ObjType.TABLE),
            self.emit_int(len(self.value) // 2, 4),
            *emission
        ]

    @staticmethod
    def make_entries(
        keys: List[Const], 
        vals: List[Const]
    ) -> List[Const]:
        if keys == []:
            return []

        k = keys[0]
        v = vals[0]

        return [k, v] + TableLit.make_entries(keys[1:], vals[1:])

    def entries_match(
        self, 
        entries: List[Const],
        other_entries: List[Const]
    ) -> bool:
        if entries == []:
            return True

        return (
            entries[0] == other_entries[0] and
            self.entries_match(entries[1:], other_entries[1:])
        )

    def __eq__(self, other: Const) -> bool:
        if not isinstance(other, TableLit):
            return False

        if len(self.value) != len(other.value):
            return False

        return self.entries_match(self.value, other.value)

    def repr_keys_and_vals(
        self,
        entries: List[Const]
    ) -> List[str]:
        if entries == []:
            return []

        key = entries[0]
        val = entries[1] 

        key = key if not isinstance(key, StrLit) else f"\"{key}\""
        val = val if not isinstance(val, StrLit) else f"\"{val}\""

        return [f"{key}: {val}"] + self.repr_keys_and_vals(entries[2:])

    def __repr__(self) -> str:
        if self.value == []:
            return "[:]"

        keys_and_vals = self.repr_keys_and_vals(self.value)

        return "".join([
            "[",
            ", ".join(keys_and_vals),
            "]"
        ])
