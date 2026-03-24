---
description: "Use when implementing Python code and tests in this repo: delivery of features/fixes across app, alembic, and tests with strong spec alignment."
applyTo: "{app,alembic,tests}/**"
---

# Delivery Instructions

## Objective
Implement production code and tests together with maximum alignment to `/spec` and repository workflow in `AGENTS.md`.

## Required Workflow
1. Confirm the target behavior from `/spec` before edits.
2. Add or update tests first when behavior is changed.
3. Implement code changes with minimal, clear diffs.
4. Run required tests (`make test`, plus focused suites when needed).
5. If blocked by ambiguity, stop and ask for clarification.

## Tooling Policy For File Operations
1. ALWAYS use VS Code / Copilot built-in tools for ALL file and workspace operations:
- Reading files: use `read_file`
- Creating files: use `create_file`
- Editing files: use `replace_string_in_file`, `multi_replace_string_in_file`, or `apply_patch`
- Searching file contents: use `grep_search` or `semantic_search`
- Finding files by name: use `file_search`
- Listing directories: use `list_dir`

NEVER use terminal commands for file operations that these tools can handle. This includes but is not limited to: `cat`, `less`, `head`, `tail`, `wc`, `grep`, `find`, `ls`, `sed`, `awk`, `touch`, `mkdir`, `echo`, `cp`, `mv`, `rm`, `tee`.

Only use the terminal (`run_in_terminal`) for operations that have no built-in tool equivalent, such as:
- Running tests, linters, or build commands
- Installing packages
- Starting/stopping servers
- Git operations (use `agent-git` whenever possible; raw `git` is not recommended and should be used only when `agent-git` cannot express the required action)

## Python and Repo Conventions
- Follow PEP 8.
- Keep imports at file top.
- Prefer module-level functions over classes unless OOP is necessary.
- Use `import module` and call `module.function()` when practical.
- Keep migrations deterministic and reviewable in `alembic/versions`.
- All tests (both unit and integration) MUST run in the container. Separate containers for other system components, and mock client/servers MAY be run along with the app for integration tests.

### Module Function Pattern
Good example
```python
# file: my_service.py
def do_smth():
    pass

# file: my_router.py
from service import my_service

def do_smth_request():
    return my_service.do_smth()
```

Bad example
```python
# file: my_service.py
class MyService:
    def do_smth(self):
        pass

# file: my_router.py
from service.my_service import MyService

def do_smth_request():
    my_service = MyService()
    return my_service.do_smth()
```

## Quality Guardrails
- No speculative refactors outside the requested scope.
- Keep performance-sensitive paths explicit (avoid hidden N+1 patterns, unnecessary loops, and redundant DB calls).
- Preserve backward compatibility unless the spec explicitly requires a contract change.
