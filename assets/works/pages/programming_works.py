"""Shared browser page shell and Geometric Calculator page (browser only).

Pure Python calculator functions live in works/programming_works.py.
"""

from pathlib import Path
import sys

if "__file__" in globals():
    _WORKS_DIR = str(Path(__file__).resolve().parent.parent)
    if _WORKS_DIR not in sys.path:
        sys.path.insert(0, _WORKS_DIR)

from programming_works import NO_INPUT_MESSAGE, area_message, to_number

try:
    import js
    from pyodide.ffi import create_proxy, to_js

    IN_BROWSER = True
except ImportError:  # plain Python (tests, tooling)
    IN_BROWSER = False

pages = {}
_keep_alive = []  # Pyodide proxies must stay referenced or the listener dies.


# --------------------------------------------------------------------------
# Page shell (browser only)
# --------------------------------------------------------------------------

def proxy(function):
    wrapped = create_proxy(function)
    _keep_alive.append(wrapped)
    return wrapped


def reduced_motion():
    return js.window.matchMedia("(prefers-reduced-motion: reduce)").matches


def current_page():
    return pages.get(str(js.window.location.hash))


def close_mobile_navigation():
    if not js.window.matchMedia("(max-width: 720px)").matches:
        return
    button = js.document.querySelector('[aria-label="Close navigation"]')
    if button is not None:
        button.click()


def navigate_to(page):
    def handler(event):
        event.preventDefault()
        js.history.pushState(None, "", f"/{page['hash']}")
        render_route()
        close_mobile_navigation()

    return handler


def add_navigation_link():
    navigation = js.document.querySelector(".menu-navigation")
    if navigation is None:
        return
    group_section = navigation.querySelector('[data-programming-group="works"]')
    if group_section is None:
        group_section = js.document.createElement("section")
        group_section.className = "menu-navigation-group"
        group_section.setAttribute("data-programming-group", "works")
        heading = js.document.createElement("p")
        heading.textContent = "Works"
        list_el = js.document.createElement("ol")
        group_section.append(heading, list_el)
        navigation.append(group_section)
    group = group_section.querySelector("ol")
    if group is None:
        return
    for page in pages.values():
        link = navigation.querySelector(f'[data-programming-link="{page["hash"]}"]')
        if link is None:
            item = js.document.createElement("li")
            link = js.document.createElement("a")
            link.href = page["hash"]
            link.setAttribute("data-programming-link", page["hash"])
            link.innerHTML = (
                '<span class="menu-navigation-item__leading">'
                f'{page["icon"]}<span>{page["label"]}</span></span>'
            )
            item.append(link)
            group.append(item)
        if link.getAttribute("data-programming-bound") != "true":
            link.setAttribute("data-programming-bound", "true")
            link.addEventListener("click", proxy(navigate_to(page)))


def stagger_page(page):
    if reduced_motion():
        return
    for index, element in enumerate(list(page.children)):
        element.style.setProperty("--page-stagger-delay", f"{index * 85}ms")
        element.classList.add("page-stagger-item")


def mount_page(definition):
    if js.document.getElementById(definition["id"]) is not None:
        return
    page = js.document.createElement("main")
    page.id = definition["id"]
    page.className = "programming-page"
    page.innerHTML = f"""
      <header class="project-route-header page-container">
        <a class="project-route-header__back-logo" href="#home" aria-label="Back to home">←</a>
        <p class="programming-page__label">{definition["eyebrow"]}</p>
      </header>
{definition["content"]}"""
    site_shell = js.document.querySelector(".site-shell")
    if site_shell is not None:
        site_shell.append(page)
    stagger_page(page)
    js.window.scrollTo(0, 0)
    definition["init"](page)


def sync_theme():
    uses_dark_theme = js.document.querySelector(".portfolio-home--dark") is not None
    for page in js.document.querySelectorAll(".programming-page"):
        page.classList.toggle("programming-page--dark", uses_dark_theme)


def sync_navigation_state():
    navigation = js.document.querySelector(".menu-navigation")
    if navigation is None:
        return
    programming_links = list(navigation.querySelectorAll("[data-programming-link]"))
    if not programming_links:
        return
    site_links = list(navigation.querySelectorAll("a:not([data-programming-link])"))
    page = current_page()
    for link in programming_links:
        is_current = page is not None and link.getAttribute("data-programming-link") == page["hash"]
        if not is_current:
            if link.hasAttribute("aria-current"):
                link.removeAttribute("aria-current")
        elif link.getAttribute("aria-current") != "page":
            link.setAttribute("aria-current", "page")
    if page is not None:
        # The site marks its own current item from its router, which does not know about these pages.
        for link in site_links:
            if link.getAttribute("aria-current") != "page":
                continue
            link.setAttribute("data-programming-hidden", "true")
            link.removeAttribute("aria-current")
        return
    site_has_current_item = any(link.getAttribute("aria-current") == "page" for link in site_links)
    for link in site_links:
        if not link.hasAttribute("data-programming-hidden"):
            continue
        link.removeAttribute("data-programming-hidden")
        if not site_has_current_item:
            link.setAttribute("aria-current", "page")


def render_route():
    portfolio = js.document.querySelector(".portfolio-home")
    page = current_page()
    for definition in pages.values():
        if definition is not page:
            stale = js.document.getElementById(definition["id"])
            if stale is not None:
                stale.remove()
    if page is not None:
        if portfolio is not None:
            portfolio.hidden = True
        mount_page(page)
        sync_theme()
        sync_navigation_state()
        return
    if portfolio is not None:
        portfolio.hidden = False
    sync_navigation_state()


def register(page):
    pages[page["hash"]] = page
    if IN_BROWSER:
        add_navigation_link()
        render_route()


# --------------------------------------------------------------------------
# Geometric calculator page (browser only)
# --------------------------------------------------------------------------

def init_geometry(page):
    state = {"shape": "circle"}
    form = page.querySelector("#area-calculator")
    result = page.querySelector("#area-result")

    def select_shape(shape):
        def handler(event):
            state["shape"] = shape
            for button in page.querySelectorAll("[data-shape]"):
                active = button.getAttribute("data-shape") == shape
                button.classList.toggle("shape-tab--active", active)
                button.setAttribute("aria-selected", "true" if active else "false")
            for fields in page.querySelectorAll("[data-fields]"):
                active = fields.getAttribute("data-fields") == shape
                fields.hidden = not active
                for field in fields.querySelectorAll("input"):
                    field.required = active
            result.textContent = NO_INPUT_MESSAGE

        return handler

    for tab in page.querySelectorAll("[data-shape]"):
        tab.addEventListener("click", proxy(select_shape(tab.getAttribute("data-shape"))))

    def read(name):
        return to_number(form.querySelector(f'[name="{name}"]').value)

    def on_submit(event):
        event.preventDefault()
        result.textContent = area_message(
            state["shape"], radius=read("radius"), base=read("base"), height=read("height")
        )

    form.addEventListener("submit", proxy(on_submit))


GEOMETRY_PAGE = {
    "hash": "#geometry",
    "id": "geometry-page",
    "label": "Geometric Calculator",
    "eyebrow": "Programming work · 01",
    "icon": '<span aria-hidden="true">◐</span>',
    "content": """
      <section class="programming-tool page-container" aria-label="Area calculator">
        <div class="programming-tool__topline"><span>Area calculator</span><span>Circle / triangle</span></div>
        <div class="shape-tabs" role="tablist" aria-label="Choose a shape">
          <button type="button" class="shape-tab shape-tab--active" role="tab" aria-selected="true" data-shape="circle">Circle</button>
          <button type="button" class="shape-tab" role="tab" aria-selected="false" data-shape="triangle">Triangle</button>
        </div>
        <form id="area-calculator" class="tool-form" novalidate>
          <div class="shape-fields" data-fields="circle">
            <label>Radius <input name="radius" type="number" min="0" step="any" inputmode="decimal" placeholder="e.g. 6" required /></label>
          </div>
          <div class="shape-fields" data-fields="triangle" hidden>
            <label>Base <input name="base" type="number" min="0" step="any" inputmode="decimal" placeholder="e.g. 8" /></label>
            <label>Height <input name="height" type="number" min="0" step="any" inputmode="decimal" placeholder="e.g. 5" /></label>
          </div>
          <button class="tool-button" type="submit">Calculate area <span aria-hidden="true">↗</span></button>
        </form>
        <output id="area-result" class="tool-result" aria-live="polite">Enter a measurement to begin.</output>
      </section>""",
    "init": init_geometry,
}


def start():
    """Watch the page so the menu link and route survive the React app re-rendering."""

    def on_mutation(*_):
        add_navigation_link()
        render_route()

    js.window.__pyodideWorksReady = True
    observer = js.MutationObserver.new(proxy(on_mutation))
    options = to_js(
        {
            "childList": True,
            "subtree": True,
            "attributes": True,
            "attributeFilter": ["class", "aria-current"],
        },
        dict_converter=js.Object.fromEntries,
    )
    observer.observe(js.document.documentElement, options)
    js.window.addEventListener("popstate", proxy(lambda *_: render_route()))
    js.window.addEventListener("hashchange", proxy(lambda *_: render_route()))


if IN_BROWSER:
    start()
register(GEOMETRY_PAGE)
