import os

from typing import List

from nevec.err.err import Err
from nevec.lex.tok import Loc

class Report:
    file_name: str
    lines: List[str]
    abs_file_path: str

    @staticmethod
    def setup(file_name: str, lines: List[str]):
        Report.file_name = file_name
        Report.lines = lines
        Report.abs_file_path = os.path.abspath(file_name)

    @staticmethod
    def err(msg: str, loc: Loc) -> Err:
        return Err(
            Report.file_name,
            Report.lines,
            msg,
            loc
        )

    @staticmethod
    def lexeme_of(loc: Loc) -> str:
        line = Report.lines[loc.line - 1]
        col = loc.col - 1

        return line[col:col + loc.length]
