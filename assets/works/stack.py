"""Stack functions, data structures, and Infix-to-Postfix converter (pure Python).

The browser visualizer page lives in works/pages/stack.py.
"""

import math

MAX_NODES = 10

PRECEDENCE = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "^": 3,
}
RIGHT_ASSOCIATIVE = {"^"}
OPERATORS = set(PRECEDENCE)


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    def __init__(self):
        self.top = None

    def push(self, data):
        new_node = Node(data)
        if self.top:
            new_node.next = self.top
        self.top = new_node

    def pop(self):
        if self.top is None:
            return None
        else:
            popped_node = self.top
            self.top = self.top.next
            popped_node.next = None
            return popped_node.data

    def peek(self):
        if self.top:
            return self.top.data
        else:
            return None

    def print_stack(self):
        if self.top is None:
            print("Stack is empty")
        else:
            current = self.top
            print("Stack elements (top → bottom):")
            while current:
                print(current.data)
                current = current.next

    def clear(self):
        """Empty the stack and return how many nodes it held."""
        removed = self.size()
        self.top = None
        return removed

    def size(self):
        count = 0
        current = self.top
        while current:
            count += 1
            current = current.next
        return count

    def values(self):
        """The values from top to bottom (for rendering in the page diagram)."""
        items = []
        current = self.top
        while current:
            items.append(current.data)
            current = current.next
        return items


def is_operand(token):
    return token not in OPERATORS and token not in ("(", ")")


def format_numeric_result(value):
    if not math.isfinite(value):
        return "Overflow"
    if float(value).is_integer():
        return f"{int(round(value)):,}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def evaluate_postfix_tokens(postfix_tokens):
    """Evaluate a list of postfix tokens using Stack when all operands are numeric.

    Returns a formatted string when numeric, 'Undefined (division by zero)' on /0,
    or None when the expression contains symbolic variables.
    """
    eval_stack = Stack()
    for token in postfix_tokens:
        if is_operand(token):
            try:
                number = float(token)
            except ValueError:
                return None
            eval_stack.push(number)
        else:
            right = eval_stack.pop()
            left = eval_stack.pop()
            if left is None or right is None:
                return None
            if token == "+":
                result = left + right
            elif token == "-":
                result = left - right
            elif token == "*":
                result = left * right
            elif token == "/":
                if right == 0:
                    return "Undefined (division by zero)"
                result = left / right
            elif token == "^":
                try:
                    result = left ** right
                except OverflowError:
                    return "Overflow"
            else:
                return None
            eval_stack.push(result)
    final_value = eval_stack.pop()
    if final_value is None:
        return None
    return format_numeric_result(final_value)


def tokenize_infix(expression):
    """Split an infix string into operand, operator, and parenthesis tokens."""
    tokens = []
    index = 0
    length = len(expression)
    while index < length:
        char = expression[index]
        if char.isspace():
            index += 1
            continue
        if char in OPERATORS or char in ("(", ")"):
            tokens.append(char)
            index += 1
            continue
        if char.isalnum() or char == "_":
            start = index
            while index < length and (
                expression[index].isalnum()
                or expression[index] in ("_", ".")
            ):
                index += 1
            tokens.append(expression[start:index])
            continue
        raise ValueError(f"Unsupported character '{char}' in expression.")
    return tokens


def should_pop_operator(stack_top, incoming):
    if stack_top is None or stack_top == "(" or stack_top not in PRECEDENCE:
        return False
    if incoming in RIGHT_ASSOCIATIVE:
        return PRECEDENCE[stack_top] > PRECEDENCE[incoming]
    return PRECEDENCE[stack_top] >= PRECEDENCE[incoming]


def infix_to_postfix_steps(expression):
    """Convert an infix expression to postfix using Stack, recording each step."""
    tokens = tokenize_infix(expression)
    if not tokens:
        raise ValueError("Enter an infix expression first.")

    # Validate basic token sequence (operands vs operators/parentheses)
    expect_operand = True
    depth = 0
    for token in tokens:
        if token == "(":
            if not expect_operand:
                raise ValueError("Unexpected '(' after operand.")
            depth += 1
        elif token == ")":
            if expect_operand:
                raise ValueError("Unexpected ')' without a preceding operand.")
            depth -= 1
            if depth < 0:
                raise ValueError("Unmatched closing parenthesis ')'.")
        elif token in OPERATORS:
            if expect_operand:
                raise ValueError(f"Unexpected operator '{token}'.")
            expect_operand = True
        else:
            if not expect_operand:
                raise ValueError(f"Missing operator before '{token}'.")
            expect_operand = False

    if expect_operand:
        raise ValueError("Expression cannot end with an operator.")
    if depth != 0:
        raise ValueError("Unclosed opening parenthesis '('.")

    op_stack = Stack()
    output = []
    steps = []

    for token_index, token in enumerate(tokens):
        if is_operand(token):
            output.append(token)
            steps.append(
                {
                    "type": "operand",
                    "token": token,
                    "token_index": token_index,
                    "stack": op_stack.values(),
                    "output": list(output),
                    "message": f"Scanned operand {token} → added to postfix output.",
                }
            )
        elif token == "(":
            op_stack.push(token)
            steps.append(
                {
                    "type": "push",
                    "token": token,
                    "token_index": token_index,
                    "stack": op_stack.values(),
                    "output": list(output),
                    "message": "Scanned '(' → pushed onto operator stack.",
                }
            )
        elif token == ")":
            while op_stack.peek() is not None and op_stack.peek() != "(":
                before_stack = op_stack.values()
                popped = op_stack.pop()
                output.append(popped)
                steps.append(
                    {
                        "type": "pop",
                        "token": token,
                        "popped": popped,
                        "token_index": token_index,
                        "before_stack": before_stack,
                        "stack": op_stack.values(),
                        "output": list(output),
                        "message": f"Closing ')': popped '{popped}' from stack to postfix output.",
                    }
                )
            before_stack = op_stack.values()
            op_stack.pop()  # discard '('
            steps.append(
                {
                    "type": "discard_paren",
                    "token": token,
                    "popped": "(",
                    "token_index": token_index,
                    "before_stack": before_stack,
                    "stack": op_stack.values(),
                    "output": list(output),
                    "message": "Matched '(' on stack → popped and discarded '('.",
                }
            )
        else:
            while should_pop_operator(op_stack.peek(), token):
                before_stack = op_stack.values()
                popped = op_stack.pop()
                output.append(popped)
                steps.append(
                    {
                        "type": "pop",
                        "token": token,
                        "popped": popped,
                        "token_index": token_index,
                        "before_stack": before_stack,
                        "stack": op_stack.values(),
                        "output": list(output),
                        "message": f"'{popped}' has ≥ precedence than '{token}' → popped '{popped}' to output.",
                    }
                )
            op_stack.push(token)
            steps.append(
                {
                    "type": "push",
                    "token": token,
                    "token_index": token_index,
                    "stack": op_stack.values(),
                    "output": list(output),
                    "message": f"Scanned operator '{token}' → pushed onto stack.",
                }
            )

    while op_stack.peek() is not None:
        before_stack = op_stack.values()
        popped = op_stack.pop()
        output.append(popped)
        steps.append(
            {
                "type": "pop",
                "token": None,
                "popped": popped,
                "token_index": len(tokens),
                "before_stack": before_stack,
                "stack": op_stack.values(),
                "output": list(output),
                "message": f"End of expression → popped remaining '{popped}' to postfix output.",
            }
        )

    return {
        "tokens": tokens,
        "postfix": " ".join(output),
        "result": evaluate_postfix_tokens(output),
        "steps": steps,
    }


def infix_to_postfix(expression):
    """Return the space-separated postfix expression for a given infix string."""
    return infix_to_postfix_steps(expression)["postfix"]


if __name__ == "__main__":
    # Create an empty stack
    stack = Stack()
    stack.print_stack()

    # Push some elements onto the stack
    stack.push(10)
    stack.push(20)
    stack.push(30)
    stack.print_stack()

    # Peek at the top element without removing it
    print("Top element:", stack.peek())

    # Pop elements off the stack
    print("Popped:", stack.pop())
    print("Popped:", stack.pop())
    stack.print_stack()

    # Pop the last element, then try popping from an empty stack
    print("Popped:", stack.pop())
    print("Popped from empty stack:", stack.pop())
    print("Peek on empty stack:", stack.peek())
    stack.print_stack()

    # Infix to Postfix conversion using Stack
    sample_infix = "10 + 20 * (3 ^ 2 - 4)"
    conversion = infix_to_postfix_steps(sample_infix)
    print(f"\nInfix:   {sample_infix}")
    print(f"Postfix: {conversion['postfix']}")
    print(f"Result:  {conversion['result']}")
