"""The layer rules from `spec/007_architecture.md`, enforced rather than reviewed.

View isolation decays invisibly: it takes one import, or one `dlg` parameter, added to a
service by someone who has not read the spec. A diff like that looks unremarkable. So the
rules ship with a check, or they do not hold — the same argument as
`tests/functional/test_tier_layout.py`, which exists because a directory convention nobody
executed had already been broken.

Two design notes:

* This parses source with `ast` and never imports. Importing plugin modules needs a QGIS
  runtime and executes Qt construction at module level, and an import-order bug in the test
  would be indistinguishable from a violation.
* Layers are named logically and mapped to paths in `LAYERS` below. Phase D moves
  `functional/api` to `api/` and so on; when it does, only that table changes.

`ALLOWED` records what is broken today so the rules can be enforced for new code immediately.
It only ever shrinks — an entry that no longer corresponds to a real violation fails the last
test here, so a fix cannot silently leave its exemption behind.
"""
import ast
from collections import defaultdict
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"

#: Logical layer -> path prefix, relative to the plugin package.
LAYERS = {
    "api": "functional/api",
    "service": "functional/service",
    "controller": "functional/controller",
    "view": "functional/view",
    "dialogs": "dialogs",
    "model": "model",
    "schema": "schema",
    "errors": "errors",
}

#: Modules that are not part of a layer yet. Phase D gives each one a home; until then they
#: are exempt rather than silently counted as something they are not.
UNCLASSIFIED = {
    "mapflow.functional.app_context",
    "mapflow.functional.auth",
    "mapflow.functional.geometry",
    "mapflow.functional.helpers",
    "mapflow.functional.layer_utils",
}

#: What each layer may depend on. Absent from a layer's set means forbidden.
MAY_IMPORT = {
    "controller": {"service", "view", "model", "schema", "errors", "dialogs"},
    "view": {"model", "schema", "errors", "dialogs"},
    "service": {"api", "service", "model", "schema", "errors"},
    "api": {"model", "schema", "errors"},
    "model": {"model", "schema", "errors"},
    "schema": {"schema", "errors"},
}

#: Parameter names that mean "a dialog was handed in". The rule that actually bites: a
#: service can drive every widget in the plugin through one of these without importing
#: anything a dependency check would notice.
DIALOG_PARAMS = {"dlg", "dialog", "maindialog", "main_dialog"}

ALLOWED = {
    # service/ and api/ importing Qt widgets — Phase C moves this to view/.
    ("widget-import", "mapflow.functional.service.alert_service"),
    ("widget-import", "mapflow.functional.service.data_catalog"),
    ("widget-import", "mapflow.functional.service.processing_service"),
    ("widget-import", "mapflow.functional.service.provider_service"),
    ("widget-import", "mapflow.functional.api.data_catalog_api"),
    # Services and two api modules taking the main dialog as a constructor argument.
    ("dialog-param", "mapflow.functional.service.area_calculator_service"),
    ("dialog-param", "mapflow.functional.service.data_catalog"),
    ("dialog-param", "mapflow.functional.service.processing_service"),
    ("dialog-param", "mapflow.functional.service.provider_service"),
    ("dialog-param", "mapflow.functional.api.data_catalog_api"),
    ("dialog-param", "mapflow.functional.api.processing_api"),
    # Reaching upwards for dialogs and views. One entry per module, so it clears only when
    # that module is clean — fixing four of five imports leaves the exemption in place.
    ("api-imports-dialogs", "mapflow.functional.api.data_catalog_api"),
    ("api-imports-dialogs", "mapflow.functional.api.processing_api"),
    ("service-imports-dialogs", "mapflow.functional.service.area_calculator_service"),
    ("service-imports-dialogs", "mapflow.functional.service.data_catalog"),
    ("service-imports-dialogs", "mapflow.functional.service.processing_service"),
    ("service-imports-view", "mapflow.functional.service.data_catalog"),
    ("service-imports-view", "mapflow.functional.service.processing_service"),
    ("view-imports-service", "mapflow.functional.view.processing_view"),
}

#: Cycles that exist today, as the set of modules involved so the entry survives a change of
#: traversal order. All three are the same shape: a package `__init__` imports its submodules
#: and a submodule imports the package back. Phase C and D dissolve both packages.
ALLOWED_CYCLES = {
    frozenset({"mapflow.dialogs", "mapflow.dialogs.main_dialog"}),
    frozenset({"mapflow.functional.service", "mapflow.functional.service.provider_service"}),
    frozenset({"mapflow.functional.service",
               "mapflow.functional.service.provider_service",
               "mapflow.functional.service.processing_service"}),
}


def module_name(path: Path) -> str:
    relative = path.relative_to(PLUGIN.parent).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve(node: ast.ImportFrom, current: str, is_package: bool) -> str:
    """Absolute target of a relative import.

    The level counts differently for a package and a plain module: inside
    ``mapflow/schema/__init__.py`` a level of 1 means ``mapflow.schema``, while inside
    ``mapflow/mapflow.py`` it means ``mapflow``. Getting this wrong resolves every relative
    import to a module that does not exist, and every rule below then passes for the wrong
    reason — which is why `test_the_resolver_handles_both_package_and_module` exists.
    """
    if node.level == 0:
        return node.module or ""
    parts = current.split(".")
    keep = len(parts) - node.level + (1 if is_package else 0)
    base = parts[:keep]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


def layer_of(module: str) -> str:
    path = module[len("mapflow."):].replace(".", "/") if module.startswith("mapflow.") else ""
    for name, prefix in LAYERS.items():
        if path == prefix or path.startswith(prefix + "/"):
            return name
    return "other"


def _sources():
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path, module_name(path), path.name == "__init__.py"


def _imports(tree, module, is_package, top_level_only=True):
    """(target, is_top_level) for every mapflow import in the file."""
    top = {id(node) for node in tree.body}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            target = resolve(node, module, is_package)
        elif isinstance(node, ast.Import):
            target = node.names[0].name
        else:
            continue
        at_top = id(node) in top
        if top_level_only and not at_top:
            continue
        yield target, at_top


def _qt_widget_imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("PyQt5.QtWidgets"):
            yield node.lineno


def _dialog_params(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for argument in node.args.args + node.args.kwonlyargs:
                if argument.arg in DIALOG_PARAMS:
                    yield node.name, argument.arg


def _parsed():
    for path, module, is_package in _sources():
        yield module, is_package, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _violations():
    """Every rule breach in the tree, as (kind, module) with a human-readable detail."""
    found = []
    for module, is_package, tree in _parsed():
        layer = layer_of(module)
        if module in UNCLASSIFIED:
            continue

        if layer in ("service", "api"):
            if any(_qt_widget_imports(tree)):
                found.append(("widget-import", module, "imports PyQt5.QtWidgets"))
            params = list(_dialog_params(tree))
            if params:
                detail = ", ".join(f"{fn}({arg})" for fn, arg in params)
                found.append(("dialog-param", module, detail))

        allowed = MAY_IMPORT.get(layer)
        if allowed is None:
            continue
        for target, _ in _imports(tree, module, is_package):
            if not target.startswith("mapflow"):
                continue
            target_layer = layer_of(target)
            if target_layer in ("other",) or target in UNCLASSIFIED:
                continue
            if target_layer not in allowed:
                found.append((f"{layer}-imports-{target_layer}", module, target))
    return found


# ---------- the resolver, tested first because everything else trusts it ----------

def test_the_resolver_handles_both_package_and_module():
    module_import = ast.parse("from .config import X").body[0]
    assert resolve(module_import, "mapflow.mapflow", is_package=False) == "mapflow.config"

    package_import = ast.parse("from .base import Y").body[0]
    assert resolve(package_import, "mapflow.schema", is_package=True) == "mapflow.schema.base"

    deep = ast.parse("from ...config import Z").body[0]
    assert resolve(deep, "mapflow.model.provider.default", is_package=False) == "mapflow.config"

    # Level 0 is an absolute import and must be returned untouched. Treating it as relative
    # silently prefixes every stdlib import with the importing module's own name, and each
    # one then classifies as a same-layer dependency — the rules pass while measuring
    # nothing, which is exactly how an earlier hand-rolled version of this reported that no
    # service imports a dialog.
    absolute = ast.parse("from typing import Optional").body[0]
    assert resolve(absolute, "mapflow.functional.api.project_api", is_package=False) == "typing"


def test_every_module_is_classified_or_listed():
    """A new package nobody wrote a rule for is how `functional/` happened."""
    stray = sorted(module for module, _is_package, _tree in _parsed()
                   if layer_of(module) == "other"
                   and module not in UNCLASSIFIED
                   and module.count(".") > 1)
    assert not stray, (
        f"modules in no layer and not listed as unclassified: {stray}. Give them a layer in "
        f"LAYERS, or add them to UNCLASSIFIED with a plan for where they go.")


# ---------- the rules ----------

def test_no_service_or_api_module_reaches_a_widget():
    """The rule that does the work. Both halves matter: a service can drive every widget in
    the plugin through a `dlg` parameter without importing anything."""
    breaches = [(kind, module, detail) for kind, module, detail in _violations()
                if kind in ("widget-import", "dialog-param")
                and (kind, module) not in ALLOWED]
    assert not breaches, "\n".join(
        f"{module}: {detail} ({kind})" for kind, module, detail in breaches)


def test_dependencies_point_downwards():
    """Includes `schema/` never importing `model/`, which is what keeps the import cycle
    deleted in b17f367 from being reintroduced by someone who never knew it existed."""
    breaches = [(kind, module, detail) for kind, module, detail in _violations()
                if "-imports-" in kind and (kind, module) not in ALLOWED]
    assert not breaches, "\n".join(
        f"{module} -> {detail} ({kind})" for kind, module, detail in breaches)


def test_there_are_no_module_level_import_cycles():
    """Only module-level imports count: a deferred import inside a function genuinely does
    not cycle, and counting it would report cycles that cannot happen."""
    known = {module for module, _is_package, _tree in _parsed()}
    graph = defaultdict(set)
    for module, is_package, tree in _parsed():
        for target, _ in _imports(tree, module, is_package):
            if target in known:
                graph[module].add(target)

    colour = defaultdict(int)
    stack, cycles = [], []

    def visit(node):
        colour[node] = 1
        stack.append(node)
        for neighbour in sorted(graph.get(node, ())):
            if colour[neighbour] == 1:
                cycles.append(stack[stack.index(neighbour):])
            elif colour[neighbour] == 0:
                visit(neighbour)
        stack.pop()
        colour[node] = 2

    for module in sorted(graph):
        if colour[module] == 0:
            visit(module)

    unexpected = [cycle for cycle in cycles if frozenset(cycle) not in ALLOWED_CYCLES]
    assert not unexpected, "import cycles:\n" + "\n".join(
        " -> ".join(cycle + [cycle[0]]) for cycle in unexpected)


def test_the_allowlist_has_no_stale_entries():
    """An exemption outliving its violation quietly re-permits what it recorded."""
    live = {(kind, module) for kind, module, _detail in _violations()}
    stale = sorted(entry for entry in ALLOWED if entry not in live)
    assert not stale, (
        f"these no longer correspond to a real violation and must be deleted from ALLOWED: "
        f"{stale}")
