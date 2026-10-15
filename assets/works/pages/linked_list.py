"""Linked list visualizer page (browser only).

Pure Python Node and LinkedList classes live in works/linked_list.py.
"""

import asyncio
from pathlib import Path
import sys

if "__file__" in globals():
    _WORKS_DIR = str(Path(__file__).resolve().parent.parent)
    if _WORKS_DIR not in sys.path:
        sys.path.insert(0, _WORKS_DIR)

from linked_list import MAX_NODES, LinkedList
from pages.programming_works import IN_BROWSER, proxy, reduced_motion, register

if IN_BROWSER:
    import js


# --------------------------------------------------------------------------
# Page (browser only)
# --------------------------------------------------------------------------

CONTENT = f"""
      <section class="programming-tool page-container" aria-label="Linked list visualizer">
        <div class="programming-tool__topline"><span>Linked list</span><span id="list-size">0 / {MAX_NODES} nodes</span></div>
        <div class="list-diagram" id="list-diagram">
          <ol class="list-track" id="list-track" aria-label="Linked list nodes"></ol>
        </div>
        <form id="linked-list-form" class="tool-form" novalidate>
          <div class="list-inputs">
            <label>Value <input name="value" type="text" maxlength="8" autocomplete="off" placeholder="e.g. 7" /></label>
            <label>Target <input name="target" type="text" maxlength="8" autocomplete="off" placeholder="e.g. 3" /></label>
          </div>
          <div class="list-actions" role="group" aria-label="Insert">
            <span class="list-actions__title" aria-hidden="true">Insert</span>
            <button type="button" class="list-button" data-action="insert-beginning">At beginning</button>
            <button type="button" class="list-button" data-action="insert-end">At end</button>
            <button type="button" class="list-button" data-action="insert-after">After target</button>
          </div>
          <div class="list-actions" role="group" aria-label="Find">
            <span class="list-actions__title" aria-hidden="true">Find</span>
            <button type="button" class="list-button" data-action="search">Search</button>
            <button type="button" class="list-button" data-action="print">Print</button>
          </div>
          <div class="list-actions" role="group" aria-label="Remove">
            <span class="list-actions__title" aria-hidden="true">Remove</span>
            <button type="button" class="list-button" data-action="delete">Remove target</button>
            <button type="button" class="list-button" data-action="clear">Clear</button>
          </div>
        </form>
        <output id="list-status" class="tool-result" aria-live="polite">The list is empty. head and tail are None.</output>
      </section>"""

ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="8" width="8" height="8" rx="1"></rect>'
    '<rect x="14" y="8" width="8" height="8" rx="1"></rect><path d="M10 12h4"></path></svg>'
)


def init(page):
    items = LinkedList()
    form = page.querySelector("#linked-list-form")
    diagram = page.querySelector("#list-diagram")
    track = page.querySelector("#list-track")
    size_label = page.querySelector("#list-size")
    status = page.querySelector("#list-status")
    value_input = form.querySelector('[name="value"]')
    target_input = form.querySelector('[name="target"]')
    run = {"id": 0}  # bumped by every action so a newer one cancels an older animation

    def say(message):
        status.textContent = message

    # Values are user text, so every node is built with textContent rather than parsed as HTML.
    def element(tag, class_name=None, text=None, decorative=False):
        node = js.document.createElement(tag)
        if class_name:
            node.className = class_name
        if text is not None:
            node.textContent = text
        if decorative:
            node.setAttribute("aria-hidden", "true")
        return node

    # Scrolls only the diagram sideways (never the page) so a new or highlighted node stays visible.
    def reveal_node(node):
        if node is None:
            return
        box = diagram.getBoundingClientRect()
        rect = node.getBoundingClientRect()
        if rect.left < box.left:
            diagram.scrollLeft = diagram.scrollLeft - (box.left - rect.left + 16)
        elif rect.right > box.right:
            diagram.scrollLeft = diagram.scrollLeft + (rect.right - box.right + 16)

    def render(enter_index=-1, active_index=-1, leave_index=-1):
        values = items.printLinkedList()
        size_label.textContent = f"{len(values)} / {MAX_NODES} nodes"
        track.replaceChildren()
        if not values:
            track.append(element("li", "list-empty", "head → None · tail → None"))
            return
        for index, value in enumerate(values):
            item = element("li", "list-node")
            if index == enter_index:
                item.classList.add("list-node--enter")
            if index == active_index:
                item.classList.add("list-node--active")
            if index == leave_index:
                item.classList.add("list-node--leave")
            tags = " · ".join(
                tag
                for tag in ("head" if index == 0 else "", "tail" if index == len(values) - 1 else "")
                if tag
            )
            box = element("span", "list-node__box")
            box.append(element("span", "list-node__data", value), element("span", "list-node__next", None, True))
            row = element("span", "list-node__row")
            row.append(box, element("span", "list-node__arrow", None, True))
            item.append(element("span", "list-node__tags", tags), row)
            track.append(item)
        none = element("li", "list-node list-node--none")
        none_row = element("span", "list-node__row")
        none_row.append(element("span", "list-node__null", "None"))
        none.append(element("span", "list-node__tags"), none_row)
        track.append(none)
        reveal_node(track.querySelector(".list-node--enter, .list-node--active"))

    def require_value():
        value = str(value_input.value).strip()
        if not value:
            say("Enter a value first.")
        return value or None

    def require_target():
        target = str(target_input.value).strip()
        if not target:
            say("Enter a target value first.")
        return target or None

    def require_room():
        if items.size() < MAX_NODES:
            return True
        say(f"The list is limited to {MAX_NODES} nodes so the diagram stays readable.")
        return False

    # Highlights nodes one by one like the while-loop in the code; skipped for reduced motion.
    # Returns False when another action started in the meantime.
    async def walk(action_id, last_index):
        if reduced_motion():
            return True
        values = items.printLinkedList()
        for index in range(last_index + 1):
            render(active_index=index)
            say(f"Checking {values[index]}…")
            await asyncio.sleep(0.38)
            if action_id != run["id"]:
                return False
        return True

    def insert_beginning():
        run["id"] += 1
        value = require_value()
        if value is None or not require_room():
            return
        items.insert_at_beginning(value)
        render(enter_index=0)
        say(f"Inserted {value} at the beginning.")
        value_input.value = ""

    def insert_end():
        run["id"] += 1
        value = require_value()
        if value is None or not require_room():
            return
        items.insert_at_end(value)
        render(enter_index=items.size() - 1)
        say(f"Inserted {value} at the end.")
        value_input.value = ""

    def insert_after():
        run["id"] += 1
        value = require_value()
        if value is None:
            return
        target = require_target()
        if target is None or not require_room():
            return
        target_index = items.find_index(target)
        if target_index == -1:
            say(f"Target {target} not found.")
            return
        items.insert_after(target, value)
        render(enter_index=target_index + 1)
        say(f"Inserted {value} after {target}.")
        value_input.value = ""

    async def search():
        run["id"] += 1
        action_id = run["id"]
        target = require_target()
        if target is None:
            return
        found_at = items.find_index(target)
        last = items.size() - 1 if found_at == -1 else found_at
        if not await walk(action_id, last):
            return
        render() if found_at == -1 else render(active_index=found_at)
        say(f"{target} not found." if found_at == -1 else f"Found {target}.")

    async def print_list():
        run["id"] += 1
        action_id = run["id"]
        values = items.printLinkedList()
        if not values:
            render()
            say("Nothing to print. The list is empty.")
            return
        if not await walk(action_id, len(values) - 1):
            return
        render()
        say(f"Printed: {' → '.join(values)}")

    async def remove():
        run["id"] += 1
        action_id = run["id"]
        target = require_target()
        if target is None:
            return
        index = items.find_index(target)
        if index == -1:
            render()
            say(f"Target {target} not found.")
            return
        if not reduced_motion():
            render(leave_index=index)
            await asyncio.sleep(0.28)
            if action_id != run["id"]:
                return
        items.delete(target)
        render()
        say(f"Removed {target}.")

    def clear():
        run["id"] += 1
        removed = items.clear()
        render()
        if removed:
            say(f"Cleared {removed} node{'' if removed == 1 else 's'}. head and tail are None.")
        else:
            say("The list is already empty.")

    def background(coroutine_function):
        # Pyodide listeners are plain callables, so start the coroutine ourselves.
        return lambda: asyncio.ensure_future(coroutine_function())

    actions = {
        "insert-beginning": insert_beginning,
        "insert-end": insert_end,
        "insert-after": insert_after,
        "search": background(search),
        "print": background(print_list),
        "delete": background(remove),
        "clear": clear,
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
    value_input.addEventListener("keydown", proxy(enter_to(insert_end)))
    target_input.addEventListener("keydown", proxy(enter_to(insert_after)))

    render()


LINKED_LIST_PAGE = {
    "hash": "#linked-list",
    "id": "linked-list-page",
    "label": "Linked List",
    "eyebrow": "Programming work · 02",
    "icon": ICON,
    "content": CONTENT,
    "init": init,
}

register(LINKED_LIST_PAGE)
