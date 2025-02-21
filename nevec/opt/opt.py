from nevec.ir.ir import *

from nevec.opt.passes import Pass
from nevec.opt.const import ConstFold
from nevec.opt.table import TablePropagation

class Opt:
    UNCONDITIONAL_PASSES: List[type[Pass]] = [
        TablePropagation
    ]

    PASSES: List[type[Pass]] = [
        ConstFold
    ]

    def __init__(self, syms: Syms, do_opt: bool):
        self.syms: Syms = syms
        
        self.all_passes: List[type[Pass]] = Opt.UNCONDITIONAL_PASSES

        if do_opt:
            self.all_passes.extend(Opt.PASSES)

    def optimize(self, ir: List[Tac]) -> List[Tac]:
        optimized = self.optimization_cycle(ir, self.all_passes)

        if optimized == ir:
            return optimized

        return self.optimize(optimized)

    def optimization_cycle(
        self,
        ir: List[Tac],
        passes: List[type[Pass]]
    ) -> List[Tac]:
        if passes == []:
            self.syms.cleanup()
            return ir

        opt_pass = passes[0](self.syms)

        opt_ir = opt_pass.optimize(ir)

        return self.optimization_cycle(opt_ir, passes[1:])
