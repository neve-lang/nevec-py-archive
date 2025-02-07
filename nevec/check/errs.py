from typing import override, List

from nevec.ast.ast import Expr, Op
from nevec.ast.type import Type

from nevec.err.err import *
from nevec.err.report import Report

from nevec.lex.tok import Loc


class Inform:
    @staticmethod 
    def at(loc: Loc, that: str) -> Note:
        return Note.harmless(loc, that)

    @staticmethod
    def type_of(what: Expr, saying="") -> Note:
        return Note.harmless(what.loc, f"{saying}: {what.type}")


class Suggest:
    @staticmethod
    def should_insert_for(what: Expr) -> bool:
        return not isinstance(what, Op)
    
    @staticmethod
    def replacement_loc_for(what: Expr) -> Loc:
        return (
            Loc.right_after(what.loc)
            if Suggest.should_insert_for(what)
            else what.loc
        )

    @staticmethod
    def method_call_for(what: Expr, suffix: str) -> str:
        if Suggest.should_insert_for(what):
            return suffix

        return f"({Report.lexeme_of(what.loc)})" + suffix

    @staticmethod
    def conversion_for(what: Expr, to: Type) -> Suggestion:
        fix = Suggest.method_call_for(what, ".somemethod")

        return Suggestion(
            f"you can convert {what.type} to {to}",
            f"converts {what.type} to {to}",
            Suggest.replacement_loc_for(what),
            fix
        )

    @staticmethod
    def possible_conversions(to: Type, *nodes: Expr) -> List[Suggestion]:
        may_be_converted = [n for n in nodes if n.type != to]
        
        return list(map(
            lambda n: Suggest.conversion_for(n, to),
            may_be_converted
        ))


class TypeErr(Err):
    def __init__(self, msg: str, locus: Loc, *exprs: Expr):
        self.msg: str = msg
        self.locus: Loc = locus
        self.exprs: List[Expr] = list(exprs)

        if self.exprs == []:
            raise ValueError(
                "at least one Expr node should be given to a TypeErr"
            )

        self.err = self.make_err()

    @override
    def emit(self) -> str:
        return self.err.emit()

    def show(self, line: Line) -> Self:
        self.err.lines.append(line)
        return self

    def add(self, note: Note, on_line: Optional[int]=None) -> Self:
        on_line = on_line if on_line is not None else note.loc.line

        lines = self.err.lines 
        found = list(filter(lambda l: l.line == on_line, lines))

        if found == []:
            line = Line(Loc(1, on_line, 1))
            line.add(note)

            self.err.lines.append(line) 
            return self

        line = found[0]
        line.add(note)

        return self

    def add_all(self, *notes: Note) -> Self:
        list(map(self.add, notes))
        return self

    def info(self, msg: str, at: Loc) -> Self:
        return self.add(
            Note.harmless(
                at,
                msg
            )
        )

    def suggest(self, *suggestion: Suggestion) -> Self:
        self.err = self.err.suggest(*suggestion)
        return self

    def make_err(self) -> Err:
        first_expr = self.exprs[0]

        first_line = Line(first_expr.loc)
        lines = self.make_lines(self.exprs, [first_line])

        lines = sorted(lines, key=lambda l: l.loc.line)

        err = Report.err(
            self.msg,
            self.locus
        )

        # wrapping it all around list() because silly Python doesn't 
        # immediately interpret map() objects
        list(map(err.show, lines))

        return err
    
    def make_lines(
        self,
        exprs: List[Expr],
        lines: List[Line],
        previous_line: Optional[int]=None
    ) -> List[Line]:
        if exprs == []:
            return lines

        head = exprs[0]
        current_line = head.loc.line

        previous_line = previous_line if previous_line else current_line

        if current_line != previous_line:
            line = Line(
                head.loc, 
                show_previous_line=current_line - 1 > previous_line
            ).add(
                Note(
                    NoteType.ERR,
                    head.loc,
                    str(head.type)
                )
            )

            return self.make_lines(
                exprs[1:],
                lines + [line],
                previous_line=current_line
            )

        last_line = lines[-1]
        last_line.add(
            Note(
                NoteType.ERR,
                head.loc,
                str(head.type)
            )
        )

        return self.make_lines(
            exprs[1:],
            lines,
            previous_line=current_line
        )


