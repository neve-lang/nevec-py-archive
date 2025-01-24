from typing import List

from enum import auto, Enum

from nevec.ast.ast import *
from nevec.ast.type import Type, Types

from nevec.ir.sym import *

from nevec.opcode.const import *
from nevec.opcode.opcode import Opcode

from nevec.lex.tok import Loc


type Ir = IExpr | IOp | Tac


class IOp:
    def __init__(self, sym: Sym, loc: Loc):
        self.sym: Sym = sym
        self.loc: Loc = loc


class IRet(IOp):
    def __repr__(self) -> str:
        return f"ret {self.sym}"


class IExpr:
    def __init__(self, type: Type, loc: Loc):
        self.type: Type = type
        self.loc: Loc = loc


class SetIExpr(IExpr):
    def __init__(self, type: Type, loc: Loc):
        self.type: Type = type
        self.loc: Loc = loc


class Tac:
    def __init__(
        self,
        sym: Sym,
        expr: IExpr | IOp,
        loc: Loc,
    ):
        self.sym: Sym = sym
        self.expr: IExpr | IOp = expr
        self.loc: Loc = loc

        # we can be 100% sure that this moment is the next moment
        # thanks to SSA
        self.moment: Moment = self.sym.first

    def next_moment(self) -> Moment:
        return self.moment + 1
    
    def __repr__(self) -> str:
        if isinstance(self.expr, IOp | SetIExpr):
            return str(self.expr)

        return f"{self.sym} = {self.expr}" 


class IUnOp(IExpr):
    class Op(Enum):
        NEG = auto() 
        NOT = auto()
        IS_NIL = auto()
        IS_NOT_NIL = auto()
        IS_ZERO = auto()
        SHOW = auto()

        def opcode(self) -> Opcode:
            return Opcode(Opcode.NEG.value + self.value - 1)


    def __init__(
        self,
        op: Op,
        operand: Tac,
        loc: Loc,
        type: Type,
    ):
        self.op: IUnOp.Op = op
        self.operand: Tac = operand

        self.loc: Loc = loc
        self.type: Type = type

    def __repr__(self) -> str:
        match self.op:
            case IUnOp.Op.NEG:
                return f"neg {self.operand.sym}"

            case IUnOp.Op.NOT:
                return f"not {self.operand.sym}"

            case IUnOp.Op.IS_NIL:
                return f"isnil {self.operand.sym}"

            case IUnOp.Op.IS_NOT_NIL:
                return f"isnotnil {self.operand.sym}"
            
            case IUnOp.Op.IS_ZERO:
                return f"isz {self.operand.sym}"

            case IUnOp.Op.SHOW:
                return f"show {self.operand.sym}"


class IBinOp(IExpr):
    class Op(Enum):
        ADD = auto()
        SUB = auto()  
        MUL = auto()
        DIV = auto()

        SHL = auto()
        SHR = auto()
        BIT_AND = auto()
        BIT_XOR = auto()
        BIT_OR = auto()

        NEQ = auto()
        EQ = auto()
        GT = auto()
        GTE = auto()
        LT = auto()
        LTE = auto()

        CONCAT = auto()

        def opcode(self) -> Opcode:
            return Opcode(Opcode.ADD.value + self.value - 1)


    def __init__(
        self,
        left: Tac,
        op: Op,
        right: Tac,
        op_lexeme: str,
        loc: Loc,
        type: Type,
    ):
        self.left: Tac = left
        self.op: IBinOp.Op = op
        self.right: Tac = right
        self.op_lexeme: str = op_lexeme

        self.loc: Loc = loc
        self.type = type

    def __repr__(self) -> str:
        if self.op_lexeme == "":
            return f"{self.left.sym} {self.right.sym}"

        return f"{self.left.sym} {self.op_lexeme} {self.right.sym}"


class TableSet(SetIExpr):
    def __init__(
        self,
        table: Tac,
        key: Tac,
        expr: Tac,
        type: Type,
        loc: Loc
    ):
        self.table: Tac = table
        self.key: Tac = key

        self.expr: Tac = expr

        self.type: Type = type
        self.loc: Loc = loc

    def __repr__(self) -> str:
        return f"{self.table.sym}[{self.key.sym}] = {self.expr.sym}"


class TableGet(IExpr):
    def __init__(
        self,
        table: Tac,
        key: Tac,
        loc: Loc,
        type: Type
    ):
        self.table: Tac = table

        self.key: Tac = key

        self.loc: Loc = loc
        self.type: Type = type

    def __repr__(self) -> str:
        return f"{self.table.sym}[{self.key.sym}]"


class IConst[T](IExpr):
    def __init__(self, value: T, loc: Loc, type: Type):
        self.value: T = value
        self.loc: Loc = loc
        self.type: Type = type

    def const(self) -> Const:
        ... 


class IInt(IConst):
    def __init__(
        self,
        value: int,
        loc: Loc,
        type: Type,
    ):
        self.value: int = value

        self.loc: Loc = loc
        self.type: Type = type

    def const(self) -> Const:
        return Num(self.value)

    def __repr__(self) -> str:
        return f"{self.value}"


class IFloat(IConst):
    def __init__(
        self,
        value: float,
        loc: Loc,
        type: Type,
    ):
        self.value: float = value

        self.loc: Loc = loc
        self.type: Type = type

    def const(self) -> Const:
        return Num(self.value)

    def __repr__(self) -> str:
        return f"{self.value}"


class IBool(IConst):
    def __init__(
        self,
        value: bool,
        loc: Loc,
    ):
        self.value: bool = value

        self.loc: Loc = loc
        self.type: Type = Types.BOOL

    def const(self) -> Const:
        return BoolLit(self.value)

    def __repr__(self) -> str:
        return str(self.value).lower()


class IStr(IConst):
    def __init__(
        self,
        value: str,
        is_interned: bool,
        loc: Loc,
        type: Type,
    ):
        self.value: str = value
        self.is_interned: bool = is_interned

        self.loc: Loc = loc
        self.type: Type = type

    def const(self) -> Const:
        value = (self.value, self.is_interned)

        return StrLit(value)

    def __repr__(self) -> str:
        return f"\"{self.value}\""


class ITable(IConst):
    def __init__(
        self,
        keys: List[IConst],
        vals: List[IConst],
        loc: Loc,
        type: Type
    ):
        self.keys = keys
        self.vals = vals

        self.loc = loc
        self.type = type

    @staticmethod
    def empty(loc: Loc, type: Type) -> "ITable":
        return ITable(
            [],
            [],
            loc,
            type
        )

    def add_entry(self, key: IConst, val: IConst):
        self.keys.append(key)
        self.vals.append(val)

    def const(self) -> Const:
        keys = [k.const() for k in self.keys]
        vals = [v.const() for v in self.vals]

        return TableLit(
            TableLit.make_entries(keys, vals)
        )

    def repr_keys_and_vals(
        self,
        keys: List[IConst],
        vals: List[IConst]
    ) -> List[str]:
        if keys == []:
            return []

        key = keys[0]
        val = vals[0]

        return [f"{key}: {val}"] + self.repr_keys_and_vals(
            keys[1:],
            vals[1:]
        )

    def __repr__(self) -> str:
        if self.keys == []:
            return "[:]"

        keys_and_vals = self.repr_keys_and_vals(self.keys, self.vals)

        return "".join([
            "[",
            ", ".join(keys_and_vals),
            "]"
        ])


class INil(IConst):
    def __init__(
        self,
        loc: Loc,
    ):
        self.loc: Loc = loc
        self.type: Type = Types.NIL

    def const(self) -> Const:
        return NilLit(None)

    def __repr__(self) -> str:
        return "nil"

