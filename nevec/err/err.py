from sys import stderr

import emoji

from enum import Enum, auto
from typing import Dict, List, Optional, Self, Tuple

from nevec.err.color import Color
from nevec.lex.tok import Loc

def join(*parts: str) -> str:
    return "".join(parts)

def offset(*parts: str, by=0) -> str:
    return " " * by + join(*parts)

def digits_in(max_line: int) -> int:
    return len(str(max_line))

class NoteType(Enum):
    HARMLESS = auto()
    ERR = auto()
    FIX = auto()


class Note:
    def __init__(self, type: NoteType, loc: Loc, msg: str):
        self.type: NoteType = type
        self.loc: Loc = loc
        self.msg: str = msg

        self.center: int = loc.true_length // 2
        self.length: int = loc.true_col + loc.true_length - 2

        self.hang: int = loc.true_col + self.center - 1

    @staticmethod
    def harmless(where: Loc, msg: str) -> "Note":
        return Note(NoteType.HARMLESS, where, msg)

    @staticmethod
    def fix(where: Loc, msg: str) -> "Note":
        return Note(NoteType.FIX, where, msg)

    @staticmethod
    def err(where: Loc, msg: str) -> "Note":
        return Note(NoteType.ERR, where, msg)

    def underline(self, col=1, initial_col=0) -> Tuple[int, str]:
        loc = self.loc

        if col == self.hang:
            next = self.underline(col + 1, initial_col)
            return (next[0] + 1, self.color() + "┬" + next[1])

        if col >= loc.true_col - 1 and col <= self.length:
            next = self.underline(col + 1, initial_col)
            return (next[0] + 1, self.color() + "─" + next[1])

        if col < loc.true_col:
            next = self.underline(col + 1, initial_col)
            return (next[0] + 1, self.color() + " " + next[1])

        return (initial_col, Color.RESET)

    def color(self) -> str:
        match self.type:
            case NoteType.HARMLESS:
                return Color.BLUE
            
            case NoteType.FIX:
                return Color.GREEN

            case NoteType.ERR:
                return Color.RED

class Line:
    def __init__(
        self, 
        loc: Loc, 
        show_previous_line=False, 
        header_msg: Optional[str]=None
    ):
        self.loc: Loc = loc
        self.notes: List[Note] = []
        self.show_previous_line: bool = show_previous_line
        self.header_msg: Optional[str] = header_msg

        self.line = loc.line
    
    def add(self, note: Note) -> Self:
        self.notes.append(note)
        return self

    def emit(
        self, 
        lines: List[str], 
        given_line: Optional[str]=None,
        given_line_number=1
    ) -> List[str]:
        self.notes = sorted(self.notes, key=lambda n: n.loc.col)

        self.get_cols()

        max_line = len(lines)

        header_msg = self.header(max_line)

        previous_line = []
        offending_line = None
        line_str = None

        if given_line is None:
            line = self.line
            line_str = str(line)

            previous_line = self.previous_line(lines, max_line)

            offending_line = lines[line - 1]
            offending_line = "".join(self.color(offending_line))
        else:
            offending_line = "".join(self.color(given_line))
            line_str = str(given_line_number)

        displayed_line = offset(
            Color.GRAY,
            line_str,
            Color.BLUE,
            " │ ",
            Color.RESET,
            offending_line,

            by=digits_in(max_line) - len(line_str)
        )

        notes = self.emit_notes(max_line)

        return [*header_msg, *previous_line, displayed_line] + notes

    def header(self, max_line: int) -> List[str]:
        if self.header_msg is None:
            return []

        header = offset(
            Color.BLUE,
            " ├─ ",
            Color.RESET,
            self.header_msg,

            by=digits_in(max_line)
        )

        return [header]

    def previous_line(self, lines: List[str], max_line: int) -> List[str]:
        if not self.show_previous_line:
            return []
        
        line = self.line - 1
        line_str = str(line)

        previous_line = lines[line - 1]
        displayed_line = offset(
            Color.GRAY,
            line_str,
            Color.BLUE,
            " │ ",
            Color.RESET,
            Color.GRAY,
            previous_line,

            by=digits_in(max_line) - len(line_str)
        )

        return [displayed_line]

    def get_cols(self):
        # i'm not sure whether i should dislike myself or Python for this
        self.colors: Dict[int, str] = {
            i: n.color()
            for n in self.notes
            for i in list(range(n.loc.col, n.loc.col + n.loc.length))
        }

        self.cols = self.colors.keys()

    def emit_notes(self, max_line: int) -> List[str]:
        head = offset(
            Color.BLUE,
            " · ",
            self.emit_underlines(),

            by=digits_in(max_line)
        )

        hangs = self.emit_hangs(self.notes, max_line)

        return [head] + hangs
        
    def emit_underlines(self, col=0, index=0) -> str:
        if index >= len(self.notes):
            return ""

        pair = self.notes[index].underline(col, col) 

        return pair[1] + self.emit_underlines(pair[0], index + 1)

    def emit_hangs(self, notes_left: List[Note], max_line: int) -> List[str]:
        def emit_each_hang(notes: List[Note], col=0) -> str:
            if notes == []:
                return ""
        
            note = notes[0] 
            if col == note.hang:
                if len(notes) == 1:
                    return note.color() + "╰" 
                
                return note.color() + "│" + emit_each_hang(notes[1:], col + 1)
            
            return " " + emit_each_hang(notes, col + 1)
        
        if notes_left == []:
            return [
                offset(Color.BLUE, " · ", Color.RESET, by=digits_in(max_line))
            ]

        tail = notes_left[-1]

        line = offset(
            Color.BLUE,
            " · ",
            emit_each_hang(notes_left),
            "─ ",
            tail.msg,
            Color.RESET,

            by=digits_in(max_line)
        )

        return [line] + self.emit_hangs(notes_left[:-1], max_line)

    def color(self, line: str, index=0, reset=False) -> List[str]:
        if index == len(line):
            if list(filter(lambda c: c > len(line), self.cols)) != []:
                return [Color.RESET, Color.GRAY, "...", Color.RESET]

            return [Color.RESET]

        col = index + 1

        if col in self.cols:
            return (
                [self.colors[col] + line[index]] + 
                self.color(line, index + 1, reset=True)
            )

        return (
            [
                (Color.RESET if reset else "") +
                line[index]
            ] + self.color(line, index + 1, reset=False)
        )


class Suggestion:
    def __init__(
        self, 
        header_msg: str, 
        fix_msg: str, 
        loc_to_replace: Loc, 
        fix: str,
        insert_if=False
    ):
        self.header_msg: str = header_msg 
        self.fix_msg: str = fix_msg
        self.loc: Loc = loc_to_replace.copy()
        self.fix: str = fix
        self.insert: bool = insert_if

        self.col: int = self.loc.col
        self.line: int = self.loc.line

        self.length: int = self.col + self.loc.length
        self.replace_length: int = self.loc.length

        self.loc.length = len(self.fix)
        self.loc.true_length = self.get_len(self.fix)

    def emit(self, lines: List[str]) -> List[str]:
        source_line = lines[self.line - 1]
        chars = list(source_line)

        chars[self.col - 1:self.col - 1] = list(self.fix)

        if not self.insert:
            chars = (
                chars[:self.col + self.loc.length - 1] +
                chars[self.col + self.loc.length - 1 + self.replace_length:]
            )
        
        modified_line = "".join(chars)

        as_line = self.as_line()

        return as_line.emit(
            lines, 
            given_line=modified_line, 
            given_line_number=self.line
        )

    def as_line(self) -> Line:
        return Line(
            self.loc,
            header_msg=self.header_msg
        ).add(
            Note.fix(
                self.loc,
                self.fix_msg
            )
        )

    def get_len(self, s: Optional[str]=None) -> int:
        s = s if s is not None else self.fix

        if len(s) == 0:
            return 0

        char = s[0]
        return 1 + int(emoji.is_emoji(char)) + self.get_len(s[1:])


class Err:
    def __init__(
        self,
        file_name: str,
        code_lines: List[str],
        msg: str,
        loc: Loc
    ):
        self.file_name: str = file_name
        self.code_lines: List[str] = code_lines
        self.msg: str = msg
        self.loc: Loc = loc

        self.lines: List[Line] = []
        self.suggestions: List[Suggestion] = []
    
    def show(self, line: Line) -> Self:
        self.lines.append(line)
        return self

    def suggest(self, *suggestions: Suggestion) -> Self:
        self.suggestions.extend(suggestions)
        return self

    def emit(self) -> str:
        max_line = len(self.code_lines)
        self.lines = self.cleanup_lines(self.lines)

        heading = offset(
            Color.RED, 
            "×  ", 
            Color.RESET,
            self.msg,

            by=digits_in(max_line)
        )

        locus = offset(
            Color.BLUE,
            " ╭─ ", 
            Color.RESET,
            self.file_name, 
            Color.GRAY,
            ":", 
            str(self.loc),
            Color.RESET,

            by=digits_in(max_line)
        )

        lines_and_suggestions = self.lines + self.suggestions

        lines = [
            "\n".join(line.emit(self.code_lines))
            for line in lines_and_suggestions
        ]

        closing_thing = offset(
            Color.BLUE,
            " ╰─ ",
            Color.RESET,

            by=digits_in(max_line)
        )

        return "\n".join([heading, locus, *lines, closing_thing])

    def cleanup_lines(self, lines: List[Line]) -> List[Line]:
        def remove_redundant_previous(
            last_line: int,
            lines: List[Line]
        ):
            if lines == []:
                return

            head = lines[0]

            if head.line == last_line + 1:
                head.show_previous_line = False

            remove_redundant_previous(head.line, lines[1:])

        sorted_lines = sorted(lines, key=lambda l: l.loc.line)
        remove_redundant_previous(1, sorted_lines)

        return sorted_lines

    def print(self):
        text = self.emit()

        print(text, file=stderr)

