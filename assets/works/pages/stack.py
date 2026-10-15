"""Stack visualizer and Infix-to-Postfix page (browser only).

Pure Python Node, Stack, and infix_to_postfix_steps live in works/stack.py.
"""

import asyncio
from pathlib import Path
import sys

if "__file__" in globals():
    _WORKS_DIR = str(Path(__file__).resolve().parent.parent)
    if _WORKS_DIR not in sys.path:
        sys.path.insert(0, _WORKS_DIR)

from pages.programming_works import IN_BROWSER, proxy, reduced_motion, register
from stack import MAX_NODES, Stack, infix_to_postfix_steps

if IN_BROWSER:
    import js


# --------------------------------------------------------------------------
# Page (browser only)
# --------------------------------------------------------------------------

CONTENT = f"""
      <section class="programming-tool page-container" aria-label="Stack visualizer and Infix to Postfix converter">
        <div class="programming-tool__topline"><span id="stack-mode-title">Stack (LIFO)</span><span id="stack-size">0 / {MAX_NODES} nodes</span></div>
        <div class="shape-tabs" role="tablist" aria-label="Choose stack mode">
          <button type="button" class="shape-tab shape-tab--active" role="tab" aria-selected="true" data-stack-mode="operations">Stack operations</button>
          <button type="button" class="shape-tab" role="tab" aria-selected="false" data-stack-mode="infix">Infix to postfix</button>
        </div>
        <div class="stack-diagram" id="stack-diagram">
          <ol class="stack-track" id="stack-track" aria-label="Stack nodes from top to bottom"></ol>
        </div>
        <div class="infix-readout" id="infix-readout" hidden>
          <div class="infix-readout__row">
            <span class="infix-readout__label">Scanning tokens</span>
            <div class="infix-tokens" id="infix-tokens">—</div>
          </div>
          <div class="infix-readout__row">
            <span class="infix-readout__label">Postfix output</span>
            <output class="infix-output" id="infix-output" aria-live="polite">—</output>
          </div>
          <div class="infix-readout__row" id="infix-result-row" hidden>
            <span class="infix-readout__label">Result</span>
            <output class="infix-output" id="infix-result" aria-live="polite">—</output>
          </div>
        </div>
        <form id="stack-form" class="tool-form" novalidate>
          <div class="stack-mode-panel" data-mode-panel="operations">
            <label>Value <input name="value" type="text" maxlength="8" autocomplete="off" placeholder="e.g. 10" /></label>
            <div class="list-actions" role="group" aria-label="Modify">
              <span class="list-actions__title" aria-hidden="true">Modify</span>
              <button type="button" class="list-button" data-action="push">Push</button>
              <button type="button" class="list-button" data-action="pop">Pop</button>
              <button type="button" class="list-button" data-action="clear">Clear</button>
            </div>
            <div class="list-actions" role="group" aria-label="Inspect">
              <span class="list-actions__title" aria-hidden="true">Inspect</span>
              <button type="button" class="list-button" data-action="peek">Peek</button>
              <button type="button" class="list-button" data-action="print">Print</button>
            </div>
          </div>
          <div class="stack-mode-panel" data-mode-panel="infix" hidden>
            <label>Infix expression <input name="infix" type="text" maxlength="64" autocomplete="off" placeholder="e.g. 10 + 20 * (3 ^ 2 - 4) or A + B * C" /></label>
            <div class="list-actions" role="group" aria-label="Infix to postfix actions">
              <span class="list-actions__title" aria-hidden="true">Convert</span>
              <button type="button" class="list-button" data-action="convert-infix">Convert</button>
              <button type="button" class="list-button" data-action="sample-infix">Load example</button>
              <button type="button" class="list-button" data-action="reset-infix">Reset</button>
            </div>
          </div>
        </form>
        <output id="stack-status" class="tool-result" aria-live="polite">Stack is empty. top is None.</output>
      </section>"""

ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="4" y="4" width="16" height="4" rx="1"></rect>'
    '<rect x="4" y="10" width="16" height="4" rx="1"></rect>'
    '<rect x="4" y="16" width="16" height="4" rx="1"></rect>'
    '</svg>'
)

EXAMPLES = [
    "10 + 20 * (3 ^ 2 - 4)",
    "A + B * (C ^ D - E)",
]


def init(page):
    stack = Stack()
    state = {"mode": "operations", "example_index": 0}
    form = page.querySelector("#stack-form")
    mode_title = page.querySelector("#stack-mode-title")
    diagram = page.querySelector("#stack-diagram")
    track = page.querySelector("#stack-track")
    size_label = page.querySelector("#stack-size")
    status = page.querySelector("#stack-status")
    value_input = form.querySelector('[name="value"]')
    infix_input = form.querySelector('[name="infix"]')
    infix_readout = page.querySelector("#infix-readout")
    infix_tokens_el = page.querySelector("#infix-tokens")
    infix_output_el = page.querySelector("#infix-output")
    infix_result_row = page.querySelector("#infix-result-row")
    infix_result_el = page.querySelector("#infix-result")
    run = {"id": 0}  # bumped by every action so a newer one cancels an older animation

    def say(message):
        status.textContent = message

    def set_eval_result(result_value):
        if result_value is None:
            infix_result_row.hidden = True
            infix_result_el.textContent = "—"
        else:
            infix_result_row.hidden = False
            infix_result_el.textContent = str(result_value)

    def element(tag, class_name=None, text=None, decorative=False):
        node = js.document.createElement(tag)
        if class_name:
            node.className = class_name
        if text is not None:
            node.textContent = text
        if decorative:
            node.setAttribute("aria-hidden", "true")
        return node

    def reveal_node(node):
        if node is None:
            return
        box = diagram.getBoundingClientRect()
        rect = node.getBoundingClientRect()
        if rect.top < box.top:
            diagram.scrollTop = diagram.scrollTop - (box.top - rect.top + 16)
        elif rect.bottom > box.bottom:
            diagram.scrollTop = diagram.scrollTop + (rect.bottom - box.bottom + 16)

    def render_values(values, enter_index=-1, active_index=-1, leave_index=-1, cap=MAX_NODES):
        if cap is not None:
            size_label.textContent = f"{len(values)} / {cap} nodes"
        else:
            size_label.textContent = f"{len(values)} operator{'' if len(values) == 1 else 's'} on stack"
        track.replaceChildren()
        if not values:
            track.append(element("li", "list-empty", "top → None"))
            return
        for index, value in enumerate(values):
            item = element("li", "stack-node")
            if index == enter_index:
                item.classList.add("stack-node--enter")
            if index == active_index:
                item.classList.add("stack-node--active")
            if index == leave_index:
                item.classList.add("stack-node--leave")
            tag_text = "top →" if index == 0 else ""
            box = element("span", "stack-node__box")
            box.append(
                element("span", "stack-node__data", str(value)),
                element("span", "stack-node__next", None, True),
            )
            row = element("span", "stack-node__row")
            if tag_text:
                row.append(element("span", "stack-node__tag", tag_text))
            row.append(box)
            item.append(row, element("span", "stack-node__arrow", None, True))
            track.append(item)
        none = element("li", "stack-node stack-node--none")
        none_row = element("span", "stack-node__row")
        none_row.append(element("span", "stack-node__null", "None"))
        none.append(none_row)
        track.append(none)
        reveal_node(track.querySelector(".stack-node--enter, .stack-node--active"))

    def render(enter_index=-1, active_index=-1, leave_index=-1):
        render_values(stack.values(), enter_index, active_index, leave_index, cap=MAX_NODES)

    def render_tokens(tokens, active_token_index=-1):
        infix_tokens_el.replaceChildren()
        if not tokens:
            infix_tokens_el.textContent = "—"
            return
        for idx, tok in enumerate(tokens):
            cls = "infix-token"
            if idx < active_token_index:
                cls += " infix-token--done"
            elif idx == active_token_index:
                cls += " infix-token--active"
            infix_tokens_el.append(element("span", cls, tok))

    def set_mode(mode):
        def handler(*_):
            run["id"] += 1
            state["mode"] = mode
            for btn in page.querySelectorAll("[data-stack-mode]"):
                active = btn.getAttribute("data-stack-mode") == mode
                btn.classList.toggle("shape-tab--active", active)
                btn.setAttribute("aria-selected", "true" if active else "false")
            for panel in page.querySelectorAll("[data-mode-panel]"):
                panel.hidden = panel.getAttribute("data-mode-panel") != mode
            if mode == "infix":
                mode_title.textContent = "Operator stack · Infix to Postfix"
                infix_readout.hidden = False
                render_values([], cap=None)
                render_tokens([])
                infix_output_el.textContent = "—"
                set_eval_result(None)
                say("Enter an infix expression with +, -, *, /, ^, or ( ) to animate conversion.")
            else:
                mode_title.textContent = "Stack (LIFO)"
                infix_readout.hidden = True
                render()
                if stack.top is None:
                    say("Stack is empty. top is None.")
                else:
                    say(f"Top element: {stack.peek()}")

        return handler

    for tab in page.querySelectorAll("[data-stack-mode]"):
        tab.addEventListener("click", proxy(set_mode(tab.getAttribute("data-stack-mode"))))

    def require_value():
        value = str(value_input.value).strip()
        if not value:
            say("Enter a value first.")
        return value or None

    def require_room():
        if stack.size() < MAX_NODES:
            return True
        say(f"The stack is limited to {MAX_NODES} nodes so the diagram stays readable.")
        return False

    async def walk(action_id, last_index):
        if reduced_motion():
            return True
        values = stack.values()
        for index in range(last_index + 1):
            render(active_index=index)
            say(f"Visiting {values[index]}…")
            await asyncio.sleep(0.38)
            if action_id != run["id"]:
                return False
        return True

    def push_node():
        run["id"] += 1
        value = require_value()
        if value is None or not require_room():
            return
        stack.push(value)
        render(enter_index=0)
        say(f"Pushed {value} onto the stack. top is now {value}.")
        value_input.value = ""

    async def pop_node():
        run["id"] += 1
        action_id = run["id"]
        if stack.top is None:
            render()
            say("Popped from empty stack: None")
            return
        if not reduced_motion():
            render(leave_index=0)
            await asyncio.sleep(0.28)
            if action_id != run["id"]:
                return
        popped = stack.pop()
        render()
        say(f"Popped: {popped}")

    def peek_node():
        run["id"] += 1
        top_value = stack.peek()
        if top_value is None:
            render()
            say("Peek on empty stack: None")
            return
        render(active_index=0)
        say(f"Top element: {top_value}")

    async def print_nodes():
        run["id"] += 1
        action_id = run["id"]
        stack.print_stack()
        values = stack.values()
        if not values:
            render()
            say("Stack is empty")
            return
        if not await walk(action_id, len(values) - 1):
            return
        render()
        say(f"Stack elements (top → bottom): {' → '.join(str(v) for v in values)}")

    def clear_nodes():
        run["id"] += 1
        removed = stack.clear()
        render()
        if removed:
            say(f"Cleared {removed} node{'' if removed == 1 else 's'}. top is None.")
        else:
            say("Stack is already empty.")

    async def convert_infix():
        run["id"] += 1
        action_id = run["id"]
        expression = str(infix_input.value).strip()
        try:
            plan = infix_to_postfix_steps(expression)
        except ValueError as exc:
            render_values([], cap=None)
            render_tokens([])
            infix_output_el.textContent = "—"
            set_eval_result(None)
            say(str(exc))
            return

        tokens = plan["tokens"]
        steps = plan["steps"]
        eval_result = plan.get("result")
        render_tokens(tokens, -1)
        render_values([], cap=None)
        infix_output_el.textContent = "—"
        set_eval_result(None)

        if not reduced_motion():
            for step in steps:
                if action_id != run["id"]:
                    return
                render_tokens(tokens, step["token_index"])
                say(step["message"])
                if step["type"] == "push":
                    render_values(step["stack"], enter_index=0, cap=None)
                    infix_output_el.textContent = " ".join(step["output"]) or "—"
                    await asyncio.sleep(0.52)
                elif step["type"] in ("pop", "discard_paren"):
                    render_values(step["before_stack"], leave_index=0, cap=None)
                    await asyncio.sleep(0.28)
                    if action_id != run["id"]:
                        return
                    render_values(step["stack"], cap=None)
                    infix_output_el.textContent = " ".join(step["output"]) or "—"
                    await asyncio.sleep(0.32)
                else:
                    render_values(step["stack"], cap=None)
                    infix_output_el.textContent = " ".join(step["output"]) or "—"
                    await asyncio.sleep(0.42)
                if action_id != run["id"]:
                    return

        render_tokens(tokens, len(tokens))
        render_values([], cap=None)
        infix_output_el.textContent = plan["postfix"]
        set_eval_result(eval_result)
        if eval_result is not None:
            say(f"Postfix result: {plan['postfix']} · Result: {eval_result}")
        else:
            say(f"Postfix result: {plan['postfix']}")

    def sample_infix():
        infix_input.value = EXAMPLES[state["example_index"] % len(EXAMPLES)]
        state["example_index"] += 1
        asyncio.ensure_future(convert_infix())

    def reset_infix():
        run["id"] += 1
        infix_input.value = ""
        render_values([], cap=None)
        render_tokens([])
        infix_output_el.textContent = "—"
        set_eval_result(None)
        say("Cleared expression. Operator stack is empty.")

    def background(coroutine_function):
        return lambda: asyncio.ensure_future(coroutine_function())

    actions = {
        "push": push_node,
        "pop": background(pop_node),
        "peek": peek_node,
        "print": background(print_nodes),
        "clear": clear_nodes,
        "convert-infix": background(convert_infix),
        "sample-infix": sample_infix,
        "reset-infix": reset_infix,
    }

    def on_click(event):
        button = event.target.closest("[data-action]")
        if button is not None:
            actions[button.getAttribute("data-action")]()

    def on_submit(event):
        event.preventDefault()

    def enter_to(action):
        def handler(event):
            if event.key != "Enter":
                return
            event.preventDefault()
            action()

        return handler

    form.addEventListener("click", proxy(on_click))
    form.addEventListener("submit", proxy(on_submit))
    value_input.addEventListener("keydown", proxy(enter_to(push_node)))
    infix_input.addEventListener("keydown", proxy(enter_to(background(convert_infix))))

    render()


STACK_PAGE = {
    "hash": "#stack",
    "id": "stack-page",
    "label": "Stacks",
    "eyebrow": "Programming work · 03",
    "icon": ICON,
    "content": CONTENT,
    "init": init,
}

register(STACK_PAGE)
