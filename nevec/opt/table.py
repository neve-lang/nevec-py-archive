from nevec.ir.ir import *
from nevec.opt.passes import Pass

class TablePropagation(Pass):
    def visit_TableSet(self, table_set: TableSet, ctx: Tac):
        key = table_set.key
        val = table_set.expr

        if not self.is_propagatable(key) or not self.is_propagatable(val):
            self.emit(ctx)
            return

        assert isinstance(key.expr, IConst) and isinstance(val.expr, IConst)

        key_sym = table_set.key.sym
        val_sym = table_set.expr.sym

        key_sym.propagate()
        val_sym.propagate()

        dest_sym = table_set.table.sym

        dest_sym.propagate()

        expr = table_set.table.expr 

        assert isinstance(expr, ITable)

        expr.add_entry(key.expr, val.expr)

        self.elim_if_dead(key_sym)
        self.elim_if_dead(val_sym)
