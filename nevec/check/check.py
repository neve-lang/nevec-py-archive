from nevec.ast.ast import *
from nevec.ast.visit import Visit

from nevec.check.errs import *

from nevec.err.err import Err

class Check(Visit[Ast, bool]):
    def __init__(self):
        self.had_err: bool = False

    def fail(self, err: Err) -> bool:
        self.had_err = True
        err.print()

        return True

    def visit_Program(self, program: Program) -> bool:
        return self.visit(program.expr)

    def visit_Parens(self, parens: Parens) -> bool: 
        return self.visit(parens.expr)

    def visit_UnOp(self, un_op: UnOp) -> bool:
        if self.visit(un_op.expr):
            return True

        expr = un_op.expr

        if un_op.op == UnOp.Op.NEG:
            if expr.type.is_num():
                return False

            un_op.type.poison()

            return self.fail(TypeErr(
                "can only negate Int or Float values",
                un_op.loc,
                expr
            ))
            
        if un_op.op == UnOp.Op.NOT:
            if expr.type == Types.BOOL:
                return False

            un_op.type.poison()

            return self.fail(TypeErr(
                "can only flip booleans",
                un_op.loc,
                expr
            ))

        raise TypeError(
            f"unary op {un_op.op.name()} not implemented in check.py"
        )
        
    def visit_Bitwise(self, bitwise: Bitwise) -> bool:
        had_err = False

        if self.visit(bitwise.left):
            bitwise.type.poison()
            return True

        if self.visit(bitwise.right):
            bitwise.type.poison()
            return True 

        if bitwise.type.is_ignorable():
            return True

        if bitwise.type == Types.UNKNOWN:
            if bitwise.left.type != bitwise.right.type:
                had_err = self.fail(TypeErr(
                    "operand types don't match",
                    bitwise.loc,
                    bitwise.left,
                    bitwise.right
                ))
            
            if (
                bitwise.left.type != Types.INT or
                bitwise.right.type != Types.INT
            ):
                had_err = self.fail(TypeErr(
                    "operands of bitwise operation must be Int",
                    bitwise.loc,
                    bitwise.left,
                    bitwise.right
                ).add(
                    Note(
                        NoteType.HARMLESS,
                        bitwise.tok.loc,
                        "only accepts Int"
                    ),
                    on_line=bitwise.loc.line
                ))

        return had_err

    def visit_Comparison(self, comparison: Comparison):
        if self.visit(comparison.left):
            comparison.type.poison()
            return True

        if self.visit(comparison.right):
            comparison.type.poison()
            return True

        if comparison.type.is_ignorable():
            return True

        if comparison.type == Types.UNKNOWN:
            return self.fail(TypeErr(
                "operand types don't match",
                comparison.loc,
                comparison.left,
                comparison.right
            ))

        return False

    def visit_Arith(self, arith: Arith):
        had_err = False

        if self.visit(arith.left):
            arith.type.poison()
            return True

        if self.visit(arith.right):
            arith.type.poison()
            return True

        if arith.type.is_ignorable():
            return True

        if arith.type == Types.UNKNOWN:
            if arith.left.type != arith.right.type:
                had_err = self.fail(TypeErr(
                    "operand types don't match",
                    arith.loc,
                    arith.left,
                    arith.right
                ))

            if (
                not arith.left.type.is_num() or
                not arith.right.type.is_num()
            ):
                had_err = self.fail(TypeErr(
                    "operands of arithmetic operation must be "
                    "either Int or Float",
                    arith.loc,
                    arith.left,
                    arith.right
                ).add(
                    Note(
                        NoteType.HARMLESS,
                        arith.tok.loc,
                        "only accepts Int or Float—assuming the types match"
                    ),
                    on_line=arith.loc.line
                ))

        return had_err

    def visit_Concat(self, concat: Concat) -> bool:
        if self.visit(concat.left):
            concat.type.poison()
            return True
    
        if self.visit(concat.right):
            concat.type.poison()
            return True

        if concat.type.is_ignorable():
            return True

        if concat.type == Types.UNKNOWN:
            left = concat.left
            right = concat.right

            # right is always the culprit, as for the parser to produce a 
            # Concat node, it must find a Str node on the left hand side
            culprit = right

            number = "".join(filter(lambda c: c.isnumeric(), left.type.name))

            # i'm endlessly sorry for this
            # i promise i'll work on refactoring everything once we implement
            # string encodings
            utf_conversion = (
                ".utf" + number
                if left.type != Types.STR
                else ".ascii"
                if culprit.type != Types.STR
                else ""
            )

            loc_to_replace = (
                Loc.right_after(culprit.loc)
                if not isinstance(culprit, Op)
                else culprit.loc
            )

            show_fix = (
                ".show" if not culprit.type.is_str() else ""
            ) + utf_conversion

            fix = (
                show_fix
                if not isinstance(culprit, Op)
                else f"({culprit})" + show_fix
            )

            if not culprit.type.is_str():
                return self.fail(TypeErr(
                    f"cannot concatenate {culprit.type} to a Str type",
                    concat.loc,
                    left,
                    right
                ).suggest(
                    Suggestion(
                        f"you can convert '{culprit}' to a Str",
                        f"converts it to {left.type} (not implemented yet)",
                        loc_to_replace,
                        fix,
                        insert_if=not isinstance(culprit, Op)
                    )
                ))
            else:
                # otherwise, culprit is a Str, but doesn't have the right 
                # encoding
                return self.fail(TypeErr(
                    f"cannot concatenate {culprit.type} to {left.type}",
                    concat.loc,
                    left,
                    right
                ).suggest(
                    Suggestion(
                        f"you can convert '{culprit}' to a {left.type}",
                        f"converts it to {left.type} (not implemented yet)",
                        loc_to_replace,
                        fix,
                        insert_if=not isinstance(culprit, Op)
                    )
                ))

        return False

    def visit_Table(self, table: Table) -> bool:
        had_err = False

        if list(
            filter(lambda k: self.visit(k), table.keys)
        ) != []:
            return True

        if list(
            filter(lambda v: self.visit(v), table.vals)
        ) != []:
            return True

        if (
            table.type.key.is_ignorable() or
            table.type.val.is_ignorable()
        ):
            return True

        if table.type.is_poisoned():
            if table.keys == []:
                return self.fail(TypeErr(
                    "could not infer table's type",
                    table.loc,
                    table
                ))

            not_ok_keys = list(filter(
                lambda k: not table.matches_first_key(k.type),
                table.keys
            ))

            not_ok_vals = list(filter(
                lambda v: not table.matches_first_val(v.type),
                table.vals
            ))

            if table.type.key.is_poisoned():
                first_key = table.keys[0]

                had_err = self.fail(TypeErr(
                    "these table keys don't match the first key's type",
                    first_key.loc,
                    *not_ok_keys
                ).add(
                    Note(
                        NoteType.HARMLESS,
                        first_key.loc,
                        f"first key: {first_key.type}"
                    ), 
                    on_line=first_key.loc.line
                ))

            if table.type.val.is_poisoned():
                first_val = table.vals[0]

                had_err = self.fail(TypeErr(
                    "these table values don't match the first value's type",
                    first_val.loc,
                    *not_ok_vals
                ).add(
                    Note(
                        NoteType.HARMLESS,
                        first_val.loc,
                        f"first value: {first_val.type}"
                    ), 
                    on_line=first_val.loc.line
                ))

        return had_err

    def visit_Int(self, i: Int) -> bool:
        _ = i
        
        return False

    def visit_Float(self, f: Float) -> bool:
        _ = f

        return False

    def visit_Bool(self, b: Bool) -> bool:
        _ = b

        return False

    def visit_Str(self, s: Str) -> bool:
        _ = s

        return False

    def visit_Interpol(self, interpol: Interpol) -> bool:
        _ = interpol

        # TODO: check if each expression implements Show
        return False

    def visit_Nil(self, nil: Nil) -> bool:
        _ = nil

        return False

    def visit_Ast(self, ast: Ast) -> bool:
        _ = ast

        return True
