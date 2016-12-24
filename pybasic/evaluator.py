from collections import deque

from more_itertools import peekable

from .tokens import Token, is_operator, is_value, get_operation, get_operator_precedence, get_string_for_token


def evaluate(code_lines):
    lineno_to_code = {}
    line_map = {}

    for line_number, line_tokens in code_lines:
        lineno_to_code[line_number] = line_tokens
    line_numbers = sorted(lineno_to_code.keys())
    for index, line_number in enumerate(line_numbers):
        line_map[line_number] = index

    context = {}
    num_lines = len(line_numbers)
    line_index = 0
    line_has_goto = False

    while True:
        line_number = line_numbers[line_index]
        line_tokens = lineno_to_code[line_number]

        token_iter = peekable(line_tokens)

        if not len(line_tokens) == 0:
            token, pos = token_iter.next()
            line_has_goto = False

            if isinstance(token, Token.Rem):
                # Skip the rest of the line, so do nothing
                pass
            elif isinstance(token, Token.Goto):
                line_has_goto = True

                try:
                    token, pos = token_iter.next()
                    if isinstance(token, Token.Number):
                        line_index = line_map.get(token.value)
                        if line_index is None:
                            raise Exception(
                                "At {}, {} invalid target line for GOTO".
                                format(line_number, pos))
                    else:
                        raise Exception(
                            "At {}, {} GOTO must be followed by valid line number".
                            format(line_number, pos))
                except StopIteration:
                    raise Exception(
                        "At {}, {} GOTO must be followed by valid line number".
                        format(line_number, pos))
            elif isinstance(token, Token.Let):
                try:
                    token, _ = token_iter.next()
                    if isinstance(token, Token.Variable):
                        name = token.name
                        token, _ = token_iter.next()
                        if isinstance(token, Token.Equals):
                            value = _parse_and_eval_expression(token_iter,
                                                               context)
                            context[name] = value
                except (StopIteration, Exception):
                    raise Exception("At {}, {} invalid syntax for LET.".format(
                        line_number, pos))
            elif isinstance(token, Token.Print):
                try:
                    value = _parse_and_eval_expression(token_iter, context)
                    print(value)
                except Exception:
                    raise Exception(
                        "At {}, {} PRINT must be followed by valid expression".
                        format(line_number, pos))
            elif isinstance(token, Token.Input):
                try:
                    token, pos = token_iter.next()
                    if isinstance(token, Token.Variable):
                        input_value = input().strip()
                        context[token.name] = input_value
                except StopIteration:
                    raise Exception(
                        "At {}, {} INPUT must be followed by a variable name".
                        format(line_number, pos))
            elif isinstance(token, Token.If):
                # Expected Next:
                # Expression THEN Number
                # Number must be a valid line number
                try:
                    value = _parse_and_eval_expression(token_iter, context)

                    if value:
                        token, pos = token_iter.next()
                        if isinstance(token, Token.Then):
                            token, pos = token_iter.next()
                            if isinstance(token, Token.Number):
                                line_has_goto = True
                                line_index = line_map.get(token.value)
                                if line_index is None:
                                    raise Exception(
                                        "At {}, {} invalid target line for THEN".
                                        format(line_number, pos))
                            else:
                                raise Exception(
                                    "At {}, {} IF must be followed by an expression and then THEN line number."
                                    .format(line_number, pos))
                        else:
                            raise Exception(
                                "At {}, {} IF must be followed by an expression and then THEN line number."
                                .format(line_number, pos))
                except (StopIteration, Exception):
                    raise Exception(
                        "At {}, {} IF must be followed by an expression and then THEN line number.".
                        format(line_number, pos))
            else:
                raise Exception("At {}, {} invalid syntax".format(line_number,
                                                                  pos))

        if not line_has_goto:
            line_index += 1
            if line_index == num_lines:
                break


def _parse_expression(token_iter):
    output_queue = deque()
    operator_stack = []

    while token_iter and not isinstance(token_iter.peek()[0], Token.Then):
        token, _ = token_iter.next()
        if is_value(token):
            output_queue.append(token)
        elif is_operator(token):
            if len(operator_stack) > 0 and is_operator(operator_stack[-1]):
                top_op = operator_stack[-1]
                if get_operator_precedence(token) <= get_operator_precedence(
                        top_op):
                    top_op = operator_stack.pop()
                    output_queue.append(top_op)
            operator_stack.append(token)
        elif isinstance(token, Token.LParen):
            operator_stack.append(token)
        elif isinstance(token, Token.RParen):
            done = False
            while not done:
                try:
                    next_token = operator_stack.pop()
                    if isinstance(next_token, Token.LParen):
                        done = True
                    else:
                        output_queue.append(next_token)
                except IndexError:
                    raise Exception("Mismatched parenthesis in expression")

    while len(operator_stack) > 0:
        next_token = operator_stack.pop()
        if isinstance(next_token, (Token.LParen, Token.RParen)):
            raise Exception("Mismatched parenthesis in expression")
        else:
            output_queue.append(next_token)

    return output_queue


def _get_value(token, context):
    if not is_value(token):
        raise Exception("Operand {} is not a value".format(str(token)))
    if isinstance(token, (Token.Number, Token.BString)):
        return token.value
    elif isinstance(token, Token.Variable):
        value = context.get(token.name, None)
        if value is None:
            raise Exception("Invalid variable {} referenced.".format(
                token.name))
        else:
            return value


def _parse_and_eval_expression(token_iter, context):
    output_queue = _parse_expression(token_iter)
    stack = []

    while len(output_queue) > 0:
        token = output_queue.popleft()
        if is_operator(token):
            if len(stack) >= 2:
                operand2_value = stack.pop()
                operand1_value = stack.pop()

                stack.append(
                    get_operation(token)(operand1_value, operand2_value))
            else:
                raise Exception("Operator {} requires two operands".format(
                    get_string_for_token(token)))
        else:
            stack.append(_get_value(token, context))

    return stack[0]
