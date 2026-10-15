// Starts the portfolio's Works pages (#geometry, #linked-list, #stack) immediately
// and loads the Python modules in works/*.py and works/pages/*.py via Pyodide.
(() => {
  const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
  const PYTHON_FILES = [
    'programming_works.py',
    'linked_list.py',
    'stack.py',
    'pages/programming_works.py',
    'pages/linked_list.py',
    'pages/stack.py',
  ];

  const MAX_NODES = 10;
  const NO_INPUT_MESSAGE = 'Enter a measurement to begin.';
  const PRECEDENCE = { '+': 1, '-': 1, '*': 2, '/': 2, '^': 3 };
  const RIGHT_ASSOCIATIVE = new Set(['^']);
  const OPERATORS = new Set(Object.keys(PRECEDENCE));
  const INFIX_EXAMPLES = ['10 + 20 * (3 ^ 2 - 4)', 'A + B * (C ^ D - E)'];

  const reducedMotion = () =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const element = (tag, className, text, decorative = false) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (decorative) node.setAttribute('aria-hidden', 'true');
    return node;
  };

  const revealNode = (diagram, node) => {
    if (!diagram || !node) return;
    const box = diagram.getBoundingClientRect();
    const rect = node.getBoundingClientRect();
    if (rect.left < box.left) {
      diagram.scrollLeft -= box.left - rect.left + 16;
    } else if (rect.right > box.right) {
      diagram.scrollLeft += rect.right - box.right + 16;
    }
  };

  const revealStackNode = (diagram, node) => {
    if (!diagram || !node) return;
    const box = diagram.getBoundingClientRect();
    const rect = node.getBoundingClientRect();
    if (rect.top < box.top) {
      diagram.scrollTop -= box.top - rect.top + 16;
    } else if (rect.bottom > box.bottom) {
      diagram.scrollTop += rect.bottom - box.bottom + 16;
    }
  };

  // --------------------------------------------------------------------------
  // 1. Geometric Calculator init
  // --------------------------------------------------------------------------
  const formatArea = (value) =>
    value
      .toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      .replace(/\.?0+$/, '');

  const areaMessage = (shape, radius = 0, base = 0, height = 0) => {
    const values = shape === 'circle' ? [radius] : [base, height];
    if (values.some((v) => !Number.isFinite(v) || v <= 0)) {
      return 'Please enter measurements greater than zero.';
    }
    if (shape === 'circle') {
      return `Circle area: ${formatArea(Math.PI * radius * radius)} square units.`;
    }
    return `Triangle area: ${formatArea(0.5 * base * height)} square units.`;
  };

  const initGeometry = (page) => {
    let currentShape = 'circle';
    const form = page.querySelector('#area-calculator');
    const result = page.querySelector('#area-result');

    page.querySelectorAll('[data-shape]').forEach((tab) => {
      tab.addEventListener('click', () => {
        currentShape = tab.getAttribute('data-shape');
        page.querySelectorAll('[data-shape]').forEach((btn) => {
          const active = btn.getAttribute('data-shape') === currentShape;
          btn.classList.toggle('shape-tab--active', active);
          btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        page.querySelectorAll('[data-fields]').forEach((fields) => {
          const active = fields.getAttribute('data-fields') === currentShape;
          fields.hidden = !active;
          fields.querySelectorAll('input').forEach((input) => {
            input.required = active;
          });
        });
        result.textContent = NO_INPUT_MESSAGE;
      });
    });

    const read = (name) => {
      const raw = (form.querySelector(`[name="${name}"]`)?.value || '').trim();
      return raw === '' ? 0 : Number(raw);
    };

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      result.textContent = areaMessage(
        currentShape,
        read('radius'),
        read('base'),
        read('height'),
      );
    });
  };

  // --------------------------------------------------------------------------
  // 2. Linked List visualizer init
  // --------------------------------------------------------------------------
  const initLinkedList = (page) => {
    let nodes = [];
    const form = page.querySelector('#linked-list-form');
    const diagram = page.querySelector('#list-diagram');
    const track = page.querySelector('#list-track');
    const sizeLabel = page.querySelector('#list-size');
    const status = page.querySelector('#list-status');
    const valueInput = form.querySelector('[name="value"]');
    const targetInput = form.querySelector('[name="target"]');
    let runId = 0;

    const say = (msg) => {
      status.textContent = msg;
    };

    const render = ({ enterIndex = -1, activeIndex = -1, leaveIndex = -1 } = {}) => {
      sizeLabel.textContent = `${nodes.length} / ${MAX_NODES} nodes`;
      track.replaceChildren();
      if (nodes.length === 0) {
        track.append(element('li', 'list-empty', 'head → None · tail → None'));
        return;
      }
      nodes.forEach((value, index) => {
        const item = element('li', 'list-node');
        if (index === enterIndex) item.classList.add('list-node--enter');
        if (index === activeIndex) item.classList.add('list-node--active');
        if (index === leaveIndex) item.classList.add('list-node--leave');
        const tags = [
          index === 0 ? 'head' : '',
          index === nodes.length - 1 ? 'tail' : '',
        ]
          .filter(Boolean)
          .join(' · ');
        const box = element('span', 'list-node__box');
        box.append(
          element('span', 'list-node__data', value),
          element('span', 'list-node__next', null, true),
        );
        const row = element('span', 'list-node__row');
        row.append(box, element('span', 'list-node__arrow', null, true));
        item.append(element('span', 'list-node__tags', tags), row);
        track.append(item);
      });
      const none = element('li', 'list-node list-node--none');
      const noneRow = element('span', 'list-node__row');
      noneRow.append(element('span', 'list-node__null', 'None'));
      none.append(element('span', 'list-node__tags', ''), noneRow);
      track.append(none);
      revealNode(diagram, track.querySelector('.list-node--enter, .list-node--active'));
    };

    const requireValue = () => {
      const value = String(valueInput.value || '').trim();
      if (!value) say('Enter a value first.');
      return value || null;
    };

    const requireTarget = () => {
      const target = String(targetInput.value || '').trim();
      if (!target) say('Enter a target value first.');
      return target || null;
    };

    const requireRoom = () => {
      if (nodes.length < MAX_NODES) return true;
      say(`The list is limited to ${MAX_NODES} nodes so the diagram stays readable.`);
      return false;
    };

    const walk = async (actionId, lastIndex) => {
      if (reducedMotion()) return true;
      for (let i = 0; i <= lastIndex; i += 1) {
        render({ activeIndex: i });
        say(`Checking ${nodes[i]}…`);
        await sleep(380);
        if (actionId !== runId) return false;
      }
      return true;
    };

    const insertBeginning = () => {
      runId += 1;
      const value = requireValue();
      if (!value || !requireRoom()) return;
      nodes.unshift(value);
      render({ enterIndex: 0 });
      say(`Inserted ${value} at the beginning.`);
      valueInput.value = '';
    };

    const insertEnd = () => {
      runId += 1;
      const value = requireValue();
      if (!value || !requireRoom()) return;
      nodes.push(value);
      render({ enterIndex: nodes.length - 1 });
      say(`Inserted ${value} at the end.`);
      valueInput.value = '';
    };

    const insertAfter = () => {
      runId += 1;
      const value = requireValue();
      if (!value) return;
      const target = requireTarget();
      if (!target || !requireRoom()) return;
      const targetIndex = nodes.indexOf(target);
      if (targetIndex === -1) {
        say(`Target ${target} not found.`);
        return;
      }
      nodes.splice(targetIndex + 1, 0, value);
      render({ enterIndex: targetIndex + 1 });
      say(`Inserted ${value} after ${target}.`);
      valueInput.value = '';
    };

    const search = async () => {
      runId += 1;
      const actionId = runId;
      const target = requireTarget();
      if (!target) return;
      if (nodes.length === 0) {
        render();
        say(`${target} not found.`);
        return;
      }
      const foundAt = nodes.indexOf(target);
      const last = foundAt === -1 ? nodes.length - 1 : foundAt;
      if (!(await walk(actionId, last))) return;
      if (foundAt === -1) {
        render();
        say(`${target} not found.`);
      } else {
        render({ activeIndex: foundAt });
        say(`Found ${target}.`);
      }
    };

    const printList = async () => {
      runId += 1;
      const actionId = runId;
      if (nodes.length === 0) {
        render();
        say('Nothing to print. The list is empty.');
        return;
      }
      if (!(await walk(actionId, nodes.length - 1))) return;
      render();
      say(`Printed: ${nodes.join(' → ')}`);
    };

    const remove = async () => {
      runId += 1;
      const actionId = runId;
      const target = requireTarget();
      if (!target) return;
      const index = nodes.indexOf(target);
      if (index === -1) {
        render();
        say(`Target ${target} not found.`);
        return;
      }
      if (!reducedMotion()) {
        render({ leaveIndex: index });
        await sleep(280);
        if (actionId !== runId) return;
      }
      nodes.splice(index, 1);
      render();
      say(`Removed ${target}.`);
    };

    const clear = () => {
      runId += 1;
      const removed = nodes.length;
      nodes = [];
      render();
      if (removed) {
        say(`Cleared ${removed} node${removed === 1 ? '' : 's'}. head and tail are None.`);
      } else {
        say('The list is already empty.');
      }
    };

    const actions = {
      'insert-beginning': insertBeginning,
      'insert-end': insertEnd,
      'insert-after': insertAfter,
      search,
      print: printList,
      delete: remove,
      clear,
    };

    form.addEventListener('click', (event) => {
      const btn = event.target.closest('[data-action]');
      if (btn) actions[btn.getAttribute('data-action')]?.();
    });
    form.addEventListener('submit', (event) => event.preventDefault());
    valueInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        insertEnd();
      }
    });
    targetInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        insertAfter();
      }
    });

    render();
  };

  // --------------------------------------------------------------------------
  // 3. Stack visualizer & Infix-to-Postfix init (vertical layout)
  // --------------------------------------------------------------------------
  const formatNumericResult = (value) => {
    if (!Number.isFinite(value)) return 'Overflow';
    if (Number.isInteger(value)) return value.toLocaleString('en-US');
    return value
      .toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 4 })
      .replace(/\.?0+$/, '');
  };

  const evaluatePostfixTokens = (postfixTokens) => {
    const evalStack = [];
    for (const token of postfixTokens) {
      if (!OPERATORS.has(token) && token !== '(' && token !== ')') {
        const num = Number(token);
        if (token.trim() === '' || Number.isNaN(num)) return null;
        evalStack.push(num);
      } else {
        const right = evalStack.pop();
        const left = evalStack.pop();
        if (left === undefined || right === undefined) return null;
        let res;
        if (token === '+') res = left + right;
        else if (token === '-') res = left - right;
        else if (token === '*') res = left * right;
        else if (token === '/') {
          if (right === 0) return 'Undefined (division by zero)';
          res = left / right;
        } else if (token === '^') {
          res = left ** right;
        } else {
          return null;
        }
        evalStack.push(res);
      }
    }
    const finalValue = evalStack.pop();
    if (finalValue === undefined) return null;
    return formatNumericResult(finalValue);
  };

  const tokenizeInfix = (expression) => {
    const tokens = [];
    let i = 0;
    while (i < expression.length) {
      const ch = expression[i];
      if (/\s/.test(ch)) {
        i += 1;
        continue;
      }
      if (OPERATORS.has(ch) || ch === '(' || ch === ')') {
        tokens.push(ch);
        i += 1;
        continue;
      }
      if (/[A-Za-z0-9_]/.test(ch)) {
        const start = i;
        while (i < expression.length && /[A-Za-z0-9_.]/.test(expression[i])) {
          i += 1;
        }
        tokens.push(expression.slice(start, i));
        continue;
      }
      throw new Error(`Unsupported character '${ch}' in expression.`);
    }
    return tokens;
  };

  const shouldPopOperator = (stackTop, incoming) => {
    if (!stackTop || stackTop === '(' || !OPERATORS.has(stackTop)) return false;
    if (RIGHT_ASSOCIATIVE.has(incoming)) {
      return PRECEDENCE[stackTop] > PRECEDENCE[incoming];
    }
    return PRECEDENCE[stackTop] >= PRECEDENCE[incoming];
  };

  const infixToPostfixSteps = (expression) => {
    const tokens = tokenizeInfix(expression);
    if (!tokens.length) throw new Error('Enter an infix expression first.');

    let expectOperand = true;
    let depth = 0;
    for (const token of tokens) {
      if (token === '(') {
        if (!expectOperand) throw new Error("Unexpected '(' after operand.");
        depth += 1;
      } else if (token === ')') {
        if (expectOperand) throw new Error("Unexpected ')' without a preceding operand.");
        depth -= 1;
        if (depth < 0) throw new Error("Unmatched closing parenthesis ')'.");
      } else if (OPERATORS.has(token)) {
        if (expectOperand) throw new Error(`Unexpected operator '${token}'.`);
        expectOperand = true;
      } else {
        if (!expectOperand) throw new Error(`Missing operator before '${token}'.`);
        expectOperand = false;
      }
    }
    if (expectOperand) throw new Error('Expression cannot end with an operator.');
    if (depth !== 0) throw new Error("Unclosed opening parenthesis '('.");

    const opStack = [];
    const output = [];
    const steps = [];

    tokens.forEach((token, tokenIndex) => {
      if (!OPERATORS.has(token) && token !== '(' && token !== ')') {
        output.push(token);
        steps.push({
          type: 'operand',
          token,
          tokenIndex,
          stack: [...opStack],
          output: [...output],
          message: `Scanned operand ${token} → added to postfix output.`,
        });
      } else if (token === '(') {
        opStack.unshift(token);
        steps.push({
          type: 'push',
          token,
          tokenIndex,
          stack: [...opStack],
          output: [...output],
          message: "Scanned '(' → pushed onto operator stack.",
        });
      } else if (token === ')') {
        while (opStack.length > 0 && opStack[0] !== '(') {
          const beforeStack = [...opStack];
          const popped = opStack.shift();
          output.push(popped);
          steps.push({
            type: 'pop',
            token,
            popped,
            tokenIndex,
            beforeStack,
            stack: [...opStack],
            output: [...output],
            message: `Closing ')': popped '${popped}' from stack to postfix output.`,
          });
        }
        const beforeStack = [...opStack];
        opStack.shift();
        steps.push({
          type: 'discard_paren',
          token,
          popped: '(',
          tokenIndex,
          beforeStack,
          stack: [...opStack],
          output: [...output],
          message: "Matched '(' on stack → popped and discarded '('.",
        });
      } else {
        while (shouldPopOperator(opStack[0], token)) {
          const beforeStack = [...opStack];
          const popped = opStack.shift();
          output.push(popped);
          steps.push({
            type: 'pop',
            token,
            popped,
            tokenIndex,
            beforeStack,
            stack: [...opStack],
            output: [...output],
            message: `'${popped}' has ≥ precedence than '${token}' → popped '${popped}' to output.`,
          });
        }
        opStack.unshift(token);
        steps.push({
          type: 'push',
          token,
          tokenIndex,
          stack: [...opStack],
          output: [...output],
          message: `Scanned operator '${token}' → pushed onto stack.`,
        });
      }
    });

    while (opStack.length > 0) {
      const beforeStack = [...opStack];
      const popped = opStack.shift();
      output.push(popped);
      steps.push({
        type: 'pop',
        token: null,
        popped,
        tokenIndex: tokens.length,
        beforeStack,
        stack: [...opStack],
        output: [...output],
        message: `End of expression → popped remaining '${popped}' to postfix output.`,
      });
    }

    return {
      tokens,
      postfix: output.join(' '),
      result: evaluatePostfixTokens(output),
      steps,
    };
  };

  const initStack = (page) => {
    let nodes = [];
    let exampleIndex = 0;
    const form = page.querySelector('#stack-form');
    const modeTitle = page.querySelector('#stack-mode-title');
    const diagram = page.querySelector('#stack-diagram');
    const track = page.querySelector('#stack-track');
    const sizeLabel = page.querySelector('#stack-size');
    const status = page.querySelector('#stack-status');
    const valueInput = form.querySelector('[name="value"]');
    const infixInput = form.querySelector('[name="infix"]');
    const infixReadout = page.querySelector('#infix-readout');
    const infixTokensEl = page.querySelector('#infix-tokens');
    const infixOutputEl = page.querySelector('#infix-output');
    const infixResultRow = page.querySelector('#infix-result-row');
    const infixResultEl = page.querySelector('#infix-result');
    let runId = 0;

    const say = (msg) => {
      status.textContent = msg;
    };

    const setEvalResult = (resultValue) => {
      if (resultValue === null || resultValue === undefined) {
        infixResultRow.hidden = true;
        infixResultEl.textContent = '—';
      } else {
        infixResultRow.hidden = false;
        infixResultEl.textContent = String(resultValue);
      }
    };

    const renderValues = (
      values,
      { enterIndex = -1, activeIndex = -1, leaveIndex = -1, cap = MAX_NODES } = {},
    ) => {
      if (cap !== null) {
        sizeLabel.textContent = `${values.length} / ${cap} nodes`;
      } else {
        sizeLabel.textContent = `${values.length} operator${values.length === 1 ? '' : 's'} on stack`;
      }
      track.replaceChildren();
      if (values.length === 0) {
        track.append(element('li', 'list-empty', 'top → None'));
        return;
      }
      values.forEach((value, index) => {
        const item = element('li', 'stack-node');
        if (index === enterIndex) item.classList.add('stack-node--enter');
        if (index === activeIndex) item.classList.add('stack-node--active');
        if (index === leaveIndex) item.classList.add('stack-node--leave');
        const tagText = index === 0 ? 'top →' : '';
        const box = element('span', 'stack-node__box');
        box.append(
          element('span', 'stack-node__data', value),
          element('span', 'stack-node__next', null, true),
        );
        const row = element('span', 'stack-node__row');
        if (tagText) {
          row.append(element('span', 'stack-node__tag', tagText));
        }
        row.append(box);
        item.append(row, element('span', 'stack-node__arrow', null, true));
        track.append(item);
      });
      const none = element('li', 'stack-node stack-node--none');
      const noneRow = element('span', 'stack-node__row');
      noneRow.append(element('span', 'stack-node__null', 'None'));
      none.append(noneRow);
      track.append(none);
      revealStackNode(diagram, track.querySelector('.stack-node--enter, .stack-node--active'));
    };

    const render = (opts = {}) => renderValues(nodes, { ...opts, cap: MAX_NODES });

    const renderTokens = (tokens, activeTokenIndex = -1) => {
      infixTokensEl.replaceChildren();
      if (!tokens.length) {
        infixTokensEl.textContent = '—';
        return;
      }
      tokens.forEach((tok, idx) => {
        let cls = 'infix-token';
        if (idx < activeTokenIndex) cls += ' infix-token--done';
        else if (idx === activeTokenIndex) cls += ' infix-token--active';
        infixTokensEl.append(element('span', cls, tok));
      });
    };

    page.querySelectorAll('[data-stack-mode]').forEach((tab) => {
      tab.addEventListener('click', () => {
        runId += 1;
        const mode = tab.getAttribute('data-stack-mode');
        page.querySelectorAll('[data-stack-mode]').forEach((btn) => {
          const active = btn.getAttribute('data-stack-mode') === mode;
          btn.classList.toggle('shape-tab--active', active);
          btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        page.querySelectorAll('[data-mode-panel]').forEach((panel) => {
          panel.hidden = panel.getAttribute('data-mode-panel') !== mode;
        });
        if (mode === 'infix') {
          modeTitle.textContent = 'Operator stack · Infix to Postfix';
          infixReadout.hidden = false;
          renderValues([], { cap: null });
          renderTokens([]);
          infixOutputEl.textContent = '—';
          setEvalResult(null);
          say('Enter an infix expression with +, -, *, /, ^, or ( ) to animate conversion.');
        } else {
          modeTitle.textContent = 'Stack (LIFO)';
          infixReadout.hidden = true;
          render();
          say(nodes.length === 0 ? 'Stack is empty. top is None.' : `Top element: ${nodes[0]}`);
        }
      });
    });

    const requireValue = () => {
      const value = String(valueInput.value || '').trim();
      if (!value) say('Enter a value first.');
      return value || null;
    };

    const requireRoom = () => {
      if (nodes.length < MAX_NODES) return true;
      say(`The stack is limited to ${MAX_NODES} nodes so the diagram stays readable.`);
      return false;
    };

    const walk = async (actionId, lastIndex) => {
      if (reducedMotion()) return true;
      for (let i = 0; i <= lastIndex; i += 1) {
        render({ activeIndex: i });
        say(`Visiting ${nodes[i]}…`);
        await sleep(380);
        if (actionId !== runId) return false;
      }
      return true;
    };

    const pushNode = () => {
      runId += 1;
      const value = requireValue();
      if (!value || !requireRoom()) return;
      nodes.unshift(value);
      render({ enterIndex: 0 });
      say(`Pushed ${value} onto the stack. top is now ${value}.`);
      valueInput.value = '';
    };

    const popNode = async () => {
      runId += 1;
      const actionId = runId;
      if (nodes.length === 0) {
        render();
        say('Popped from empty stack: None');
        return;
      }
      if (!reducedMotion()) {
        render({ leaveIndex: 0 });
        await sleep(280);
        if (actionId !== runId) return;
      }
      const popped = nodes.shift();
      render();
      say(`Popped: ${popped}`);
    };

    const peekNode = () => {
      runId += 1;
      if (nodes.length === 0) {
        render();
        say('Peek on empty stack: None');
        return;
      }
      render({ activeIndex: 0 });
      say(`Top element: ${nodes[0]}`);
    };

    const printNodes = async () => {
      runId += 1;
      const actionId = runId;
      if (nodes.length === 0) {
        render();
        say('Stack is empty');
        return;
      }
      if (!(await walk(actionId, nodes.length - 1))) return;
      render();
      say(`Stack elements (top → bottom): ${nodes.join(' → ')}`);
    };

    const clearNodes = () => {
      runId += 1;
      const removed = nodes.length;
      nodes = [];
      render();
      if (removed) {
        say(`Cleared ${removed} node${removed === 1 ? '' : 's'}. top is None.`);
      } else {
        say('Stack is already empty.');
      }
    };

    const convertInfix = async () => {
      runId += 1;
      const actionId = runId;
      const expression = String(infixInput.value || '').trim();
      let plan;
      try {
        plan = infixToPostfixSteps(expression);
      } catch (err) {
        renderValues([], { cap: null });
        renderTokens([]);
        infixOutputEl.textContent = '—';
        setEvalResult(null);
        say(err.message);
        return;
      }

      const { tokens, steps, postfix, result: evalResult } = plan;
      renderTokens(tokens, -1);
      renderValues([], { cap: null });
      infixOutputEl.textContent = '—';
      setEvalResult(null);

      if (!reducedMotion()) {
        for (const step of steps) {
          if (actionId !== runId) return;
          renderTokens(tokens, step.tokenIndex);
          say(step.message);
          if (step.type === 'push') {
            renderValues(step.stack, { enterIndex: 0, cap: null });
            infixOutputEl.textContent = step.output.join(' ') || '—';
            await sleep(520);
          } else if (step.type === 'pop' || step.type === 'discard_paren') {
            renderValues(step.beforeStack, { leaveIndex: 0, cap: null });
            await sleep(280);
            if (actionId !== runId) return;
            renderValues(step.stack, { cap: null });
            infixOutputEl.textContent = step.output.join(' ') || '—';
            await sleep(320);
          } else {
            renderValues(step.stack, { cap: null });
            infixOutputEl.textContent = step.output.join(' ') || '—';
            await sleep(420);
          }
          if (actionId !== runId) return;
        }
      }

      renderTokens(tokens, tokens.length);
      renderValues([], { cap: null });
      infixOutputEl.textContent = postfix;
      setEvalResult(evalResult);
      if (evalResult !== null && evalResult !== undefined) {
        say(`Postfix result: ${postfix} · Result: ${evalResult}`);
      } else {
        say(`Postfix result: ${postfix}`);
      }
    };

    const sampleInfix = () => {
      infixInput.value = INFIX_EXAMPLES[exampleIndex % INFIX_EXAMPLES.length];
      exampleIndex += 1;
      convertInfix();
    };

    const resetInfix = () => {
      runId += 1;
      infixInput.value = '';
      renderValues([], { cap: null });
      renderTokens([]);
      infixOutputEl.textContent = '—';
      setEvalResult(null);
      say('Cleared expression. Operator stack is empty.');
    };

    const actions = {
      push: pushNode,
      pop: popNode,
      peek: peekNode,
      print: printNodes,
      clear: clearNodes,
      'convert-infix': convertInfix,
      'sample-infix': sampleInfix,
      'reset-infix': resetInfix,
    };

    form.addEventListener('click', (event) => {
      const btn = event.target.closest('[data-action]');
      if (btn) actions[btn.getAttribute('data-action')]?.();
    });
    form.addEventListener('submit', (event) => event.preventDefault());
    valueInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        pushNode();
      }
    });
    infixInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        convertInfix();
      }
    });

    render();
  };

  // --------------------------------------------------------------------------
  // Page Definitions & Instant Router
  // --------------------------------------------------------------------------
  const PAGES = {
    '#geometry': {
      hash: '#geometry',
      id: 'geometry-page',
      label: 'Geometric Calculator',
      eyebrow: 'Programming work · 01',
      icon: '<span aria-hidden="true">◐</span>',
      content: `
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
      </section>`,
      init: initGeometry,
    },
    '#linked-list': {
      hash: '#linked-list',
      id: 'linked-list-page',
      label: 'Linked List',
      eyebrow: 'Programming work · 02',
      icon: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="8" width="8" height="8" rx="1"></rect><rect x="14" y="8" width="8" height="8" rx="1"></rect><path d="M10 12h4"></path></svg>',
      content: `
      <section class="programming-tool page-container" aria-label="Linked list visualizer">
        <div class="programming-tool__topline"><span>Linked list</span><span id="list-size">0 / ${MAX_NODES} nodes</span></div>
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
      </section>`,
      init: initLinkedList,
    },
    '#stack': {
      hash: '#stack',
      id: 'stack-page',
      label: 'Stacks',
      eyebrow: 'Programming work · 03',
      icon: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="4" rx="1"></rect><rect x="4" y="10" width="16" height="4" rx="1"></rect><rect x="4" y="16" width="16" height="4" rx="1"></rect></svg>',
      content: `
      <section class="programming-tool page-container" aria-label="Stack visualizer and Infix to Postfix converter">
        <div class="programming-tool__topline"><span id="stack-mode-title">Stack (LIFO)</span><span id="stack-size">0 / ${MAX_NODES} nodes</span></div>
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
      </section>`,
      init: initStack,
    },
  };

  const staggerPage = (page) => {
    if (reducedMotion()) return;
    Array.from(page.children).forEach((child, index) => {
      child.style.setProperty('--page-stagger-delay', `${index * 85}ms`);
      child.classList.add('page-stagger-item');
    });
  };

  const syncTheme = () => {
    const usesDarkTheme = document.querySelector('.portfolio-home--dark') !== null;
    document.querySelectorAll('.programming-page').forEach((page) => {
      page.classList.toggle('programming-page--dark', usesDarkTheme);
    });
  };

  const syncNavigationState = () => {
    const navigation = document.querySelector('.menu-navigation');
    if (!navigation) return;
    const programmingLinks = Array.from(navigation.querySelectorAll('[data-programming-link]'));
    if (!programmingLinks.length) return;
    const siteLinks = Array.from(navigation.querySelectorAll('a:not([data-programming-link])'));
    const page = PAGES[window.location.hash];

    for (const link of programmingLinks) {
      const isCurrent = Boolean(page && link.getAttribute('data-programming-link') === page.hash);
      if (!isCurrent) {
        if (link.hasAttribute('aria-current')) link.removeAttribute('aria-current');
      } else if (link.getAttribute('aria-current') !== 'page') {
        link.setAttribute('aria-current', 'page');
      }
    }

    if (page) {
      for (const link of siteLinks) {
        if (link.getAttribute('aria-current') !== 'page') continue;
        link.setAttribute('data-programming-hidden', 'true');
        link.removeAttribute('aria-current');
      }
      return;
    }

    const siteHasCurrentItem = siteLinks.some((link) => link.getAttribute('aria-current') === 'page');
    for (const link of siteLinks) {
      if (!link.hasAttribute('data-programming-hidden')) continue;
      link.removeAttribute('data-programming-hidden');
      if (!siteHasCurrentItem) {
        link.setAttribute('aria-current', 'page');
      }
    }
  };

  const mountPage = (definition) => {
    if (document.getElementById(definition.id)) return;
    const siteShell = document.querySelector('.site-shell');
    if (!siteShell) return;
    const page = document.createElement('main');
    page.id = definition.id;
    page.className = 'programming-page';
    page.innerHTML = `
      <header class="project-route-header page-container">
        <a class="project-route-header__back-logo" href="#home" aria-label="Back to home">←</a>
        <p class="programming-page__label">${definition.eyebrow}</p>
      </header>
${definition.content}`;
    siteShell.append(page);
    staggerPage(page);
    window.scrollTo(0, 0);
    definition.init(page);
  };

  const renderRoute = () => {
    if (window.__pyodideWorksReady) return;
    const portfolio = document.querySelector('.portfolio-home');
    const page = PAGES[window.location.hash];
    for (const definition of Object.values(PAGES)) {
      if (definition !== page) {
        document.getElementById(definition.id)?.remove();
      }
    }
    if (page) {
      if (portfolio && !portfolio.hidden) portfolio.hidden = true;
      mountPage(page);
      syncTheme();
      syncNavigationState();
      return;
    }
    if (portfolio && portfolio.hidden) portfolio.hidden = false;
    syncNavigationState();
  };

  const ensureWorksNavigation = () => {
    if (window.__pyodideWorksReady) return;
    const navigation = document.querySelector('.menu-navigation');
    if (!navigation) return;

    let groupSection = navigation.querySelector('[data-programming-group="works"]');
    if (!groupSection) {
      groupSection = document.createElement('section');
      groupSection.className = 'menu-navigation-group';
      groupSection.setAttribute('data-programming-group', 'works');

      const heading = document.createElement('p');
      heading.textContent = 'Works';

      const listEl = document.createElement('ol');
      groupSection.append(heading, listEl);
      navigation.append(groupSection);
    }

    const listEl = groupSection.querySelector('ol');
    if (!listEl) return;

    for (const item of Object.values(PAGES)) {
      let link = navigation.querySelector(`[data-programming-link="${item.hash}"]`);
      if (!link) {
        const li = document.createElement('li');
        link = document.createElement('a');
        link.href = item.hash;
        link.setAttribute('data-programming-link', item.hash);
        link.innerHTML = `<span class="menu-navigation-item__leading">${item.icon}<span>${item.label}</span></span>`;
        link.addEventListener('click', (event) => {
          if (link.getAttribute('data-programming-bound') === 'true') return;
          event.preventDefault();
          history.pushState(null, '', `/${item.hash}`);
          renderRoute();
          if (window.matchMedia('(max-width: 720px)').matches) {
            document.querySelector('[aria-label="Close navigation"]')?.click();
          }
        });
        li.append(link);
        listEl.append(li);
      }
    }
  };

  const syncAll = () => {
    ensureWorksNavigation();
    renderRoute();
  };

  syncAll();
  window.addEventListener('DOMContentLoaded', syncAll);
  window.addEventListener('hashchange', renderRoute);
  window.addEventListener('popstate', renderRoute);
  new MutationObserver(syncAll).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'aria-current'],
  });

  const loadScript = (src) =>
    new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Could not load ${src}`));
      document.head.append(script);
    });

  const start = async () => {
    await loadScript(`${PYODIDE_URL}pyodide.js`);
    const pyodide = await window.loadPyodide({ indexURL: PYODIDE_URL });
    try {
      pyodide.FS.mkdirTree('pages');
    } catch {
      try {
        pyodide.FS.mkdir('pages');
      } catch {}
    }
    pyodide.FS.writeFile('pages/__init__.py', '');
    for (const file of PYTHON_FILES) {
      const response = await fetch(`/assets/works/${file}`, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`Could not load /assets/works/${file} (${response.status})`);
      }
      pyodide.FS.writeFile(file, await response.text());
    }
    await pyodide.runPythonAsync(`
import importlib, sys
if "." not in sys.path:
    sys.path.insert(0, ".")
importlib.invalidate_caches()
import pages.programming_works, pages.linked_list, pages.stack
`);
  };

  start().catch((error) => console.error('Python pages failed to start:', error));
})();
