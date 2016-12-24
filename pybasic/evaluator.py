from .tokens import Token

from more_itertools import peekable


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

            if type(token) == Token.Rem:
                # Skip the rest of the line, so do nothing
                pass
            elif type(token) == Token.Goto:
                line_has_goto = True

                try:
                    token, pos = token_iter.next()
                    if type(token) == Token.Number:
                        line_index = line_map.get(token.value)
                        if line_index is None:
                            raise Exception("At {}, {} invalid target line for GOTO".format(line_number, pos))
                    else:
                        raise Exception("At {}, {} GOTO must be followed by valid line number".format(line_number, pos))
                except StopIteration:
                    raise Exception("At {}, {} GOTO must be followed by valid line number".format(line_number, pos))
            elif type(token) == Token.Let:
                try:
                    token, _ = token_iter.next()
                    if type(token) == Token.Variable:
                        name = token.name
                        token, _ = token_iter.next()
                        if type(token) == Token.Equals:
                            value = parse_and_eval_expression(token_iter, context)
                            context[name] = value
                except (StopIteration, Exception):
                    raise Exception("At {}, {} invalid syntax for LET.".format(line_number, pos))
            elif type(token) == Token.Print:
                try:
                    value = parse_and_eval_expression(token_iter, context)
                    print(value)
                except Exception:
                    raise Exception("At {}, {} PRINT must be followed by valid expression".format(line_number, pos))
            elif type(token) == Token.Input:
                try:
                    token, pos = token_iter.next()
                    if type(token) == Token.Variable:
                        input_value = input().strip()
                        context[token.name] = input_value
                except StopIteration:
                    raise Exception("At {}, {} INPUT must be followed by a variable name".format(line_number, pos))
            elif type(token) == Token.If:
                # Expected Next:
                # Expression THEN Number
                # Number must be a valid line number
                pass
            else:
                raise Exception("At {}, {} invalid syntax".format(line_number, pos))

        if not line_has_goto:
            line_index += 1
            if line_index == num_lines:
                break


def parse_and_eval_expression(token_iter, context):
    # Default Value
    result = ""

    try:
        token, pos = token_iter.next()

        if type(token) == Token.Number:
            result = token.value
        elif type(token) == Token.Variable:
            result = context.get(token.name, None)
            if result is None:
                raise Exception("At {}, invalid variable reference in expression: {}".format(pos, token.name))
        elif type(token) == Token.BString:
            result = token.value
        elif type(token) == Token.Minus:
            result = parse_and_eval_expression(token_iter, context)
            if type(result) == int:
                result = -result
            else:
                raise Exception("At {}, can only negate numerical expressions".format(pos))
        elif type(token) == Token.Bang:
            result = parse_and_eval_expression(token_iter, context)
            if type(result) == bool:
                result = not result
            else:
                raise Exception("At {}, boolean not only works against boolean expressions".format(pos))
        else:
            raise Exception("Unimplemented")
    except StopIteration:
        raise Exception("Empty expression")

    return result
