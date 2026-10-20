"""Source-located Lark AST for the combinational TritVerilog language."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lark import Lark, Token, Tree, UnexpectedInput


GRAMMAR = r"""
start: module+
module: "module" NAME parameter_header? "(" ports? ")" ";" item* "endmodule"
parameter_header: "#" "(" parameter_entry ("," parameter_entry)* ")"
parameter_entry: "parameter" "integer"? NAME "=" expr
ports: port ("," port)*
port: DIRECTION "reg"? "trit" range? NAME -> typed_port
    | NAME                         -> continued_port
range: "[" expr ":" expr "]"
?item: wire_decl | parameter_decl | localparam_decl | genvar_decl | assign
     | primitive | instance | generate | for_generate | always_comb
wire_decl: ("wire" | "reg") "trit" range? NAME ("," NAME)* ";"
always_comb: "always" "@" ("(" "*" ")" | "*") statement
?statement: "begin" statement* "end" -> block
          | "if" "(" expr ")" statement ("else" statement)? -> if_stmt
          | "case" "(" expr ")" case_item* "endcase" -> case_stmt
          | expr "=" expr ";" -> blocking
          | ";" -> empty_stmt
case_item: expr ("," expr)* ":" statement -> labeled_case
         | "default" ":"? statement -> default_case
parameter_decl: "parameter" "integer"? bindings ";"
localparam_decl: "localparam" "integer"? bindings ";"
bindings: binding ("," binding)*
binding: NAME "=" expr
genvar_decl: "genvar" NAME ("," NAME)* ";"
assign: "assign" expr "=" expr ";"
primitive: PRIMITIVE NAME "(" expr ("," expr)* ")" ";"
instance: NAME overrides? NAME "(" connections? ")" ";"
overrides: "#" "(" named_value ("," named_value)* ")"
connections: named_value ("," named_value)*
named_value: "." NAME "(" expr ")"
generate: "generate" item* "endgenerate"
for_generate: "for" "(" "genvar"? NAME "=" expr ";" expr ";" step ")" "begin" ":" NAME item* "end"
step: NAME "=" expr -> step_assign
    | NAME "++"     -> step_inc
    | NAME "--"     -> step_dec
?expr: conditional
?conditional: logical_or "?" expr ":" conditional -> conditional
            | logical_or
?logical_or: logical_or "||" logical_and -> logical_or
           | logical_and
?logical_and: logical_and "&&" bit_or -> logical_and
            | bit_or
?bit_or: bit_or "|" bit_and -> max_op
       | bit_and
?bit_and: bit_and "&" equality -> min_op
        | equality
?equality: equality EQ relation -> comparison
         | relation
?relation: relation REL shift -> comparison
         | shift
?shift: shift LSHIFT sum -> shift_left
      | shift RSHIFT sum -> shift_right
      | sum
?sum: sum "+" product -> add
    | sum "-" product -> sub
    | product
?product: product "*" unary -> mul
        | product "/" unary -> div
        | product "%" unary -> mod
        | unary
?unary: "~" unary -> neg
      | "!" unary -> logical_not
      | "-" unary -> minus
      | "+" unary -> plus
      | atom
?atom: TRIT -> trit
     | INT -> integer
     | NAME "(" expr "," expr ")" -> call
     | NAME select? -> ref
     | "{" expr ("," expr)* "}" -> concat
     | "(" expr ")"
select: "[" expr "]" -> bit_select
      | "[" expr ":" expr "]" -> part_select
DIRECTION.2: /(?:input|output)\b/
PRIMITIVE.2: /(?:inv|nand|nor|nany|buf)\b/
EQ: "==" | "!="
REL: "<=" | ">=" | "<" | ">"
LSHIFT.2: "<<<" | "<<"
RSHIFT.2: ">>>" | ">>"
TRIT: /[0-9]+'[tT][A-Za-z0-9_]+/
INT: /[0-9]+/
NAME: /[a-zA-Z_][a-zA-Z_0-9$]*/ | /\\[^\s]+/
%import common.WS
%ignore WS
%ignore /\/\/[^\n]*/
%ignore /(?s:\/\*.*?\*\/)/
"""

_PARSER = Lark(GRAMMAR, parser="lalr", propagate_positions=True)


class HDLError(ValueError):
    """A syntax or circuit error with a stable file:line:column prefix."""


@dataclass(frozen=True)
class Location:
    filename: str
    line: int
    column: int

    def error(self, message: str) -> HDLError:
        return HDLError(f"{self.filename}:{self.line}:{self.column}: {message}")


@dataclass
class Module:
    name: str
    tree: Tree
    filename: str

    def location(self, node: Tree | Token | None = None) -> Location:
        obj = node if node is not None else self.tree
        meta = obj.meta if isinstance(obj, Tree) else obj
        return Location(self.filename, meta.line, meta.column)


@dataclass
class AST:
    modules: dict[str, Module]


def identifier(token: Token | str) -> str:
    return str(token).removeprefix("\\")


def parse(text: str, filename: str = "<string>") -> AST:
    """Parse source without evaluating parameters or connecting circuit nets."""
    try:
        tree = _PARSER.parse(text)
    except UnexpectedInput as exc:
        context = exc.get_context(text).strip()
        raise HDLError(
            f"{filename}:{exc.line}:{exc.column}: invalid TritVerilog syntax "
            f"(combinational trit logic; use always @* and blocking = assignments)\n{context}"
        ) from None
    modules = {}
    for node in tree.children:
        name = identifier(node.children[0])
        module = Module(name, node, filename)
        if name in modules:
            raise module.location().error(f"duplicate module {name!r}")
        modules[name] = module
    return AST(modules)


def read_sources(paths: str | Path | list[str | Path]) -> AST:
    """Read modules and relative `include files, preserving original locations."""
    modules: dict[str, Module] = {}
    visited: set[Path] = set()

    def read(path: Path, active: set[Path]) -> None:
        path = path.resolve()
        if path in active:
            raise HDLError(f"{path}:1:1: recursive `include")
        if path in visited:
            return
        source = path.read_text()
        # Blank comments for directive discovery; keep offsets and newlines.
        masked = re.sub(r"//[^\n]*|/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m[0]), source, flags=re.S)
        includes = list(re.finditer(r'`include\s+"([^"\n]+)"', masked))
        for match in includes:
            read(path.parent / match[1], active | {path})
        for match in reversed(includes):
            source = source[:match.start()] + re.sub(r"[^\n]", " ", match[0]) + source[match.end():]
        ast = parse(source, str(path))
        for name, module in ast.modules.items():
            if name in modules:
                raise module.location().error(f"duplicate module {name!r}")
            modules[name] = module
        visited.add(path)

    for path in [paths] if isinstance(paths, (str, Path)) else paths:
        read(Path(path), set())
    return AST(modules)
