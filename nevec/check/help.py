from typing import Callable, List, Optional, Self

from nevec.ast.ast import Ast, Expr, Op
from nevec.ast.type import Type

from nevec.check.errs import TypeErr

from nevec.lex.tok import Loc

from nevec.err.err import Note, Suggestion, Err
from nevec.err.report import Report

class Assume:
    def __init__(
        self,
        node: Expr, 
        that: Type | Callable[[Type], bool],
        is_complete: bool=True
    ):
        self.node: Expr = node

        self.complete_with(that)

        self.is_complete: bool = is_complete

        self.nodes_in_question: List[Expr] = [node]
        self.types_in_question: List[Type] = [node.type]

    @staticmethod
    def same_type(a: Expr, b: Expr) -> "Assume":
        return Assume(a, lambda t: t == b.type).with_nodes(b)

    @staticmethod
    def both(a: Expr, b: Expr) -> "Assume":
        return Assume(a, lambda t: t == b.type, is_complete=False).with_nodes(b)

    @staticmethod
    def that(what: bool) -> "Assume":
        return Assume(Expr.empty(), lambda _: what).without()

    def complete_with(self, what: Type | Callable[[Type], bool]):
        self.what = self.make_what(what)

        self.is_complete = True

    def make_what(self, what: Type | Callable[[Type], bool]):
        if isinstance(what, Type):
            return lambda t: t == what
        else:
            return what

    def with_nodes(self, *nodes: Expr) -> Self:
        self.nodes_in_question.extend(nodes)
        return self.with_types(*[n.type for n in nodes])

    def with_types(self, *types: Type) -> Self:
        self.types_in_question.extend(types)
        return self

    def with_only(self, *nodes: Expr) -> Self:
        self.without()

        return self.with_nodes(*nodes)

    def without(self) -> Self:
        self.nodes_in_question = []
        self.types_in_question = []

        return self

    def are(self, what: Type | Callable[[Type], bool]) -> Self:
        old_what = self.what

        what = self.make_what(what)

        new_what = lambda t: old_what(t) and what(t)
        self.complete_with(new_what)

        return self

    def otherwise(self, err: Err) -> bool:
        if not self.is_complete:
            raise ValueError("usage of incomplete Assum-ption")

        if self.what(self.node.type):
            return False

        err.print()
        return True

    def or_fail(
        self, 
        *details: Note | Suggestion,
        at: Optional[Loc]=None, 
        saying: Optional[str]=None
    ) -> bool:
        if self.what(self.node.type):
            return False

        first_node = self.nodes_in_question[0]

        at = at if at is not None else first_node.loc

        types = [t for t in self.types_in_question]

        first_few_types = types[:2]

        saying = (
            saying
            if saying is not None
            else f"mismatched types: {', '.join(map(str, first_few_types))}"
        )

        notes = [d for d in details if isinstance(d, Note)]
        suggestions = [d for d in details if isinstance(d, Suggestion)]

        return self.otherwise(
            TypeErr(
                saying,
                at,
                *self.nodes_in_question
            ).add_all(*notes).suggest(*suggestions)
        )

    def or_show(self, msg: str, parent: Ast, *culprits: Expr) -> bool:
        return self.otherwise(
            TypeErr(
                msg,
                parent.loc,
                *culprits
            )
        )


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


