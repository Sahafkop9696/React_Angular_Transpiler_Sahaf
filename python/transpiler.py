


from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class StateVar:
    name: str
    setter: str
    init: str


def read_source(path: Path) -> str:
    return path.read_text()


def extract_component_name(source: str) -> str:
    match = re.search(r"function\s+(\w+)\s*\(", source)
    if not match:
        raise ValueError("Could not find component function definition")
    return match.group(1)


def extract_use_state(source: str) -> List[StateVar]:
    pattern = re.compile(
        r"const\s+\[(\w+)\s*,\s*(\w+)\]\s*=\s*useState\((.*?)\);", re.DOTALL
    )
    states: List[StateVar] = []
    for name, setter, init in pattern.findall(source):
        states.append(StateVar(name=name, setter=setter, init=init.strip()))
    return states


def extract_handlers(source: str) -> dict:
    """
    Capture simple arrow-function handlers: const addTodo = () => { ... };
    """
    handlers = {}
    pattern = re.compile(r"const\s+(\w+)\s*=\s*\(\s*\)\s*=>\s*\{([\s\S]*?)\};")
    for name, body in pattern.findall(source):
        handlers[name] = body.strip()
    return handlers


def extract_jsx_return(source: str) -> str:
    match = re.search(r"return\s*\(([\s\S]*?)\);", source)
    if not match:
        raise ValueError("Could not find JSX return block")
    return match.group(1).strip()


def infer_ts_type(init: str) -> str:
    init_stripped = init.strip()
    if re.match(r"^['\"].*['\"]$", init_stripped):
        return "string"
    if re.match(r"^\[\s*\]$", init_stripped):
        return "any[]"
    if re.match(r"^\[\s*(['\"].*['\"]\s*(,\s*['\"].*['\"]\s*)*)\]$", init_stripped):
        return "string[]"
    if re.match(r"^\d+(\.\d+)?$", init_stripped):
        return "number"
    return "any"


def sanitize_init(init: str) -> str:
    """
    Keep initializers intact; minor touch-ups for TS compatibility.
    """
    return init.strip()


def rewrite_handler_body(body: str, states: List[StateVar]) -> str:
    setters = {s.setter: s.name for s in states}
    rewritten = body

    # Replace setter calls with direct assignment (simple heuristic)
    for setter, var in setters.items():
        rewritten = re.sub(
            rf"{setter}\s*\(\s*\[([^\]]+)\]\s*\)",
            rf"this.{var} = [\1]",
            rewritten,
        )
        rewritten = re.sub(
            rf"{setter}\s*\(\s*([^)]+)\)",
            rf"this.{var} = \1",
            rewritten,
        )

    # Prefix state vars with this.
    for state in states:
        rewritten = re.sub(
            rf"(?<!this\.)\b{state.name}\b", rf"this.{state.name}", rewritten
        )

    return rewritten


def js_to_kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def convert_map_expression(match: re.Match) -> str:
    collection = match.group(1)
    item = match.group(2)
    index = match.group(3)
    body = match.group(4).strip()

    # Remove key attribute if present and extract inner HTML of <li>
    inner_match = re.search(r"<li[^>]*>([\s\S]*?)</li>", body)
    inner = inner_match.group(1).strip() if inner_match else body
    inner = re.sub(r"\{(\w+)\}", r"{{ \1 }}", inner)

    return f'<li *ngFor="let {item} of {collection}; let {index} = index">{inner}</li>'


def convert_jsx_to_template(jsx: str, states: List[StateVar]) -> str:
    template = jsx
    setter_lookup = {s.setter: s.name for s in states}

    # Convert map -> *ngFor (narrow pattern for todos.map((todo, index) => (<li>...</li>)))
    template = re.sub(
        r"\{(\w+)\.map\(\((\w+),\s*(\w+)\)\s*=>\s*\(([\s\S]*?)\)\)\}",
        convert_map_expression,
        template,
    )

    # Controlled input -> ngModel
    def input_repl(match: re.Match) -> str:
        attrs = match.group(1)
        value_match = re.search(r"value=\{(\w+)\}", attrs)
        setter_call = re.search(r"onChange=\{\s*\(.*?=>\s*(set\w+)\(", attrs, re.S)
        if value_match and setter_call:
            setter_name = setter_call.group(1)
            state_name = setter_lookup.get(setter_name)
            if not state_name:
                # Fallback: decapitalize setter suffix
                suffix = setter_name[3:]
                state_name = suffix[0].lower() + suffix[1:]
            return f'<input [(ngModel)]="{state_name}" type="text" />'
        return f"<input {attrs}/>"

    template = re.sub(r"<input([\s\S]*?)/>", input_repl, template)

    # Event handlers
    template = re.sub(r'onClick=\{(\w+)\}', r'(click)="\1()"', template)
    template = template.replace("className", "class")

    # Interpolations for remaining {expr}
    template = re.sub(r"\{([\w\.]+)\}", r"{{ \1 }}", template)

    # Minor cleanup: remove double braces in attributes that may have slipped through
    template = re.sub(r"\s+key=\{\w+\}", "", template)
    return template.strip()


def generate_ts(component: str, states: List[StateVar], handlers: dict) -> str:
    selector = js_to_kebab(component)
    lines = [
        "import { Component } from '@angular/core';",
        "",
        "@Component({",
        f"  selector: 'app-{selector}',",
        f"  templateUrl: './{component}.component.html',",
        f"  styleUrls: ['./{component}.component.css']",
        "})",
        f"export class {component}Component {{",
    ]

    for state in states:
        lines.append(
            f"  {state.name}: {infer_ts_type(state.init)} = {sanitize_init(state.init)};"
        )

    if states:
        lines.append("")

    for name, body in handlers.items():
        lines.append(f"  {name}() {{")
        body_lines = []
        current_indent = 0
        for raw_line in rewrite_handler_body(body, states).splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("}"):
                current_indent = max(current_indent - 1, 0)
            body_lines.append("  " * current_indent + stripped)
            if stripped.endswith("{"):
                current_indent += 1

        for line in body_lines:
            lines.append(f"    {line}")
        lines.append("  }")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    lines.append("}")
    return "\n".join(lines)


def write_output(component: str, ts_code: str, template: str) -> None:
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{component}.component.ts").write_text(ts_code + "\n")
    (out_dir / f"{component}.component.html").write_text(template + "\n")


def transpile(react_path: Path) -> None:
    source = read_source(react_path)
    component = extract_component_name(source)
    states = extract_use_state(source)
    handlers = extract_handlers(source)
    jsx = extract_jsx_return(source)

    ts_code = generate_ts(component, states, handlers)
    template = convert_jsx_to_template(jsx, states)

    write_output(component, ts_code, template)
    print(f"Generated Angular component for {component} in ./output")


if __name__ == "__main__":
    transpile(Path("react/TodoList.jsx"))
