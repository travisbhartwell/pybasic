from collections import deque

from more_itertools import peekable

from .tokens import (Token, Associativity, is_operator, is_unary_operator,
                     is_value, get_operation, get_operator_associativity,
                     get_operator_precedence, get_string_for_token)


def _raise_error(message, line_number, pos):
    raise Exception("At {}, {} {}".format(line_number, pos, message))


def evaluate(code_lines):
    lineno_to_code = dict(code_lines)
    line_numbers = sorted(lineno_to_code.keys())
    line_map = dict([(b, a) for (a, b) in enumerate(line_numbers)])

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
                            _raise_error("invalid target line for GOTO",
                                         line_number,
                                         pos)
                    else:
                        _raise_error("GOTO must be followed by valid line number",
                                     line_number,
                                     pos)
                except StopIteration:
                    _raise_error("GOTO must be followed by valid line number",
                                 line_number,
                                 pos)
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
                except (StopIteration, ExpressionEvalException):
                    _raise_error("invalid syntax for LET.",
                                 line_number,
                                 pos)
            elif isinstance(token, Token.Print):
                try:
                    value = _parse_and_eval_expression(token_iter, context)
                    print(value)
                except ExpressionEvalException:
                    _raise_error("PRINT must be followed by valid expression",
                                 line_number,
                                 pos)
            elif isinstance(token, Token.Input):
                try:
                    token, pos = token_iter.next()
                    if isinstance(token, Token.Variable):
                        input_value = input().strip()
                        context[token.name] = input_value
                except StopIteration:
                    _raise_error("INPUT must be followed by a variable name",
                                 line_number,
                                 pos)
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
                                    _raise_error("invalid target line for THEN",
                                                 line_number,
                                                 pos)
                            else:
                                _raise_error("Should be: IF expression THEN line number",
                                             line_number,
                                             pos)
                        else:
                            _raise_error("Should be: IF expression THEN line number",
                                         line_number,
                                         pos)
                except (StopIteration, ExpressionEvalException):
                    _raise_error("Should be: IF expression THEN line number",
                                 line_number,
                                 pos)
            else:
                _raise_error("Invalid syntax",
                             line_number,
                             pos)

        if not line_has_goto:
            line_index += 1
            if line_index == num_lines:
                break


class ExpressionEvalException(Exception):
    pass


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
                associativity = get_operator_associativity(token)

                if (associativity == Associativity.Left and
                    get_operator_precedence(token) <= get_operator_precedence(top_op)) or \
                        (associativity == Associativity.Right and
                         get_operator_precedence(token) < get_operator_precedence(top_op)):
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
                    raise ExpressionEvalException("Mismatched parenthesis in expression")

    while len(operator_stack) > 0:
        next_token = operator_stack.pop()
        if isinstance(next_token, (Token.LParen, Token.RParen)):
            raise ExpressionEvalException("Mismatched parenthesis in expression")
        else:
            output_queue.append(next_token)

    return output_queue


def _get_value(token, context):
    if not is_value(token):
        raise ExpressionEvalException("Operand {} is not a value".format(str(token)))
    if isinstance(token, (Token.Number, Token.BString)):
        return token.value
    elif isinstance(token, Token.Variable):
        value = context.get(token.name, None)
        if value is None:
            raise ExpressionEvalException("Invalid variable {} referenced.".format(
                token.name))
        else:
            return value


def _parse_and_eval_expression(token_iter, context):
    output_queue = _parse_expression(token_iter)
    stack = []

    while len(output_queue) > 0:
        token = output_queue.popleft()
        if is_unary_operator(token):
            if len(stack) >= 1:
                operand_value = stack.pop()

                stack.append(
                    get_operation(token)(operand_value))
            else:
                raise ExpressionEvalException("Operator {} requires an operand".format(
                    get_string_for_token(token)))
        elif is_operator(token):
            if len(stack) >= 2:
                operand2_value = stack.pop()
                operand1_value = stack.pop()

                stack.append(
                    get_operation(token)(operand1_value, operand2_value))
            else:
                raise ExpressionEvalException("Operator {} requires two operands".format(
                    get_string_for_token(token)))
        else:
            stack.append(_get_value(token, context))

    # If the expression is well-formed, there should only be the result on the stack
    assert len(stack) == 1
    return stack[0]
