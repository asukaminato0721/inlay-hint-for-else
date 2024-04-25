import ast
import unittest
from collections import OrderedDict
from typing import List, Literal, Sequence, Tuple


class IfElifVisitor(ast.NodeVisitor):
    def __init__(self):
        self.conditions: List[Tuple[Literal["if", "elif", "else"], int, int, str]] = []

    def visit_If(self, node: ast.If):
        condition = ast.unparse(node.test)  # Python >= 3.9
        self.conditions.append(("if", node.lineno, node.col_offset, condition))
        for e in node.orelse:
            if isinstance(e, ast.If):  # Checking if the node is a chained if (elif)
                condition = ast.unparse(e.test)  # Python >= 3.9
                self.conditions.append(("elif", e.lineno, e.col_offset, condition))
            else:
                self.conditions.append(("else", e.lineno, e.col_offset, "tbd"))
        self.generic_visit(node)


def extract_conditions(code: str):
    tree = ast.parse(code)
    visitor = IfElifVisitor()
    visitor.visit(tree)
    return visitor.conditions


def merge(conds: Sequence[Tuple[Literal["if", "elif", "else"], int, int, str]]):
    ans: List[Tuple[int, int, str]] = []
    cur: OrderedDict[str, bool] = OrderedDict()  # use OrderedDict as ordered set
    for node, line, offset, stmt in conds:
        if node == "if":
            cur[stmt] = True
        if node == "elif":
            cur[stmt] = True
        if node == "else":
            cond = " and ".join(f"(not ({stmt}))" for stmt in cur.keys())
            ans.append((line - 2, offset, cond))
            cur.clear()
    return ans


class Test(unittest.TestCase):
    def test_if(self):
        code = """\
if x > 0:
    x = x + 1
elif x == 0:
    x = x - 1
else:
    x = 0
a=2 # confusing
if y:
    ...
elif y:
    ...
elif y:...
else:...

if z:...
if k:...
x=2# confusing
y=3# confusing

        """
        self.assertListEqual(
            extract_conditions(code),
            [
                ("if", 1, 0, "x > 0"),
                ("elif", 3, 0, "x == 0"),
                ("if", 3, 0, "x == 0"),
                ("else", 6, 4, "tbd"),  # one more line
                ("if", 8, 0, "y"),
                ("elif", 10, 0, "y"),
                ("if", 10, 0, "y"),
                ("elif", 12, 0, "y"),
                ("if", 12, 0, "y"),
                ("else", 13, 5, "tbd"),  # one more line
                ("if", 15, 0, "z"),
                ("if", 16, 0, "k"),
            ],
        )

    def test_merge(self):
        code = """\
if x > 0:
    x = x + 1
elif x == 0:
    x = x - 1
else:
    x = 0
a=2 # confusing
if y:
    ...
elif y:
    ...
elif y:
    ...
else:
    ...

if z:
    ...
if k:
    ...
x=2# confusing
y=3# confusing

        """
        self.assertListEqual(
            merge(extract_conditions(code)),
            [(4, 4, "(not (x > 0)) and (not (x == 0))"), (13, 4, "(not (y))")],
        )

    def test_merge_nest(self):
        code = """\
if x > 0:
    x = x + 1
elif x == 0:
    x = x - 1
else:
    x = 0
a=2 # confusing

if y1:
    ...
elif y2:
    ...
else:
    if y3:
        ...
    else:
        ...

if z:
    ...
if k:
    ...
x=2# confusing
y=3# confusing

        """
        self.assertListEqual(
            merge(extract_conditions(code)),
            [
                (4, 4, "(not (x > 0)) and (not (x == 0))"),
                (15, 8, "(not (y1)) and (not (y2)) and (not (y3))"),
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
