"""Find (and with --fix, rewrite) Qt enum names that only Qt 5 accepts.

Qt 6 (QGIS 4) accepts only scoped enums: `Qt.AlignmentFlag.AlignLeft`, not `Qt.AlignLeft`. Qt 5
(QGIS 3) accepts both, so the scoped form keeps the plugin working in both. The enum each name
belongs to is looked up in PyQt6, so this needs `pip install PyQt6` (QGIS itself isn't needed).

    python tools/qt6_check.py mapflow_next tests          # report; exit code 1 if anything is found
    python tools/qt6_check.py --fix mapflow_next tests    # rewrite Class.Member to Class.Enum.Member

It also reports enum members read from an instance (`action.NoRole`), which Qt 6 doesn't allow
and which can't be rewritten automatically, and calls to exec_(), which PyQt6 removed.
"""
import ast
import enum
import io
import sys
import tokenize
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtNetwork, QtSvg, QtSvgWidgets, QtTest, QtWidgets

CLASSES, ENUM_TYPES, MEMBERS = {}, set(), set()
for _module in (QtCore, QtGui, QtWidgets, QtNetwork, QtSvg, QtSvgWidgets, QtTest):
    for _name in dir(_module):
        _cls = getattr(_module, _name)
        if isinstance(_cls, type) and (_name.startswith("Q") or _name == "Qt"):
            CLASSES.setdefault(_name, _cls)
            for _attr in dir(_cls):
                try:
                    _obj = getattr(_cls, _attr)
                except Exception:                       # noqa: BLE001
                    continue
                if isinstance(_obj, type) and issubclass(_obj, enum.Enum):
                    ENUM_TYPES.add(_attr)
                    MEMBERS.update(_obj.__members__)


def _enums_of(cls):
    for attr in dir(cls):
        try:
            obj = getattr(cls, attr)
        except Exception:                               # noqa: BLE001
            continue
        if isinstance(obj, type) and issubclass(obj, enum.Enum):
            yield attr, obj


def scoped(class_name, member):
    """(replacement, problem) for Class.member."""
    cls = CLASSES[class_name]
    if hasattr(cls, member):
        return None, None
    found = [name for name, kind in _enums_of(cls) if member in kind.__members__]
    if len(found) == 1:
        return f"{class_name}.{found[0]}.{member}", None
    return None, ("ambiguous: " + "/".join(found)) if found else "not in PyQt6"


def unscoped(source):
    """[(start, end, replacement or None, problem)] for every Class.Member outside import lines."""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    found, in_import = [], False
    for i in range(len(tokens) - 2):
        a, dot, b = tokens[i], tokens[i + 1], tokens[i + 2]
        if a.type in (tokenize.NEWLINE, tokenize.ENDMARKER):
            in_import = False
        elif a.type == tokenize.NAME and a.string in ("import", "from") and (
                i == 0 or tokens[i - 1].type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT)):
            in_import = True
        if in_import or a.type != tokenize.NAME or a.string not in CLASSES or dot.string != "." \
                or b.type != tokenize.NAME or (i and tokens[i - 1].string == "."):
            continue
        replacement, problem = scoped(a.string, b.string)
        if replacement or problem:
            found.append((a.start, b.end, replacement, problem))
    return found


def instance_access(source):
    """`something.Member` where `something` is an object, not the enum: lines and text."""
    out = []
    tree = ast.parse(source)
    modules = {alias.asname or alias.name.split(".")[0] for node in ast.walk(tree)
               if isinstance(node, ast.Import) for alias in node.names}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in MEMBERS and node.attr[:1].isupper():
            root = node.value
            while isinstance(root, ast.Attribute):
                root = root.value
            if not isinstance(root, ast.Name) or root.id.lstrip("_")[:1].isupper() or root.id in modules:
                continue                                # a class or an alias of one (Qt.…, _Error.…), or a module
            out.append((node.lineno, f"{ast.unparse(node)}: an enum read from an object; Qt 6 wants Class.Enum.Member"))
        if isinstance(node, ast.Attribute) and node.attr == "exec_":
            out.append((node.lineno, f"{ast.unparse(node)}(): PyQt6 has only exec()"))
    return out


def main(argv):
    fix = "--fix" in argv
    paths = []
    for arg in (a for a in argv if not a.startswith("--")):
        path = Path(arg)
        paths += sorted(p for p in path.rglob("*.py") if "qt6_shim" not in p.parts) if path.is_dir() else [path]
    issues = fixed = 0
    for path in paths:
        source = path.read_text()
        found = unscoped(source)
        edits = [(s, e, r) for s, e, r, _ in found if r]
        for (row, _), _, replacement, problem in found:
            if problem or not fix:
                print(f"{path}:{row}: {replacement or problem}")
                issues += 1
        if fix and edits:
            lines = source.splitlines(keepends=True)
            for (row, col), (_, end_col), text in sorted(edits, reverse=True):
                lines[row - 1] = lines[row - 1][:col] + text + lines[row - 1][end_col:]
            path.write_text("".join(lines))
            fixed += len(edits)
        for row, text in instance_access(path.read_text()):
            print(f"{path}:{row}: {text}")
            issues += 1
    if fix:
        print(f"{fixed} enum names scoped")
    print(f"{issues} Qt 6 issues" if issues else "No Qt 6 issues found")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
