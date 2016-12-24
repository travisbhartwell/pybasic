from .tokens import Token, get_token_for_string, is_value

from collections import namedtuple
import itertools

from more_itertools import peekable

TokenAndPos = namedtuple('TokenAndPos', ['token', 'pos'])

LineOfCode = namedtuple('LineOfCode', ['line_number', 'tokens'])


def _is_int(n):
    try:
        int(n)
        return True
    except ValueError:
        return False


def _is_valid_identifier(ident):
    if not isinstance(ident, str):
        return False
    if len(ident) == 1:
        return ident.isalpha()
    else:
        if not (ident[0] == '_' or ident[0].isalpha()):
            return False

        for c in ident[1:]:
            if not (c == '_' or c.isalnum()):
                return False

    return True


def _takewhile_peek(predicate, iterable):
    """
    Alternate implementation of itertools.takewhile() that uses peek.
    """
    while True:
        p = iterable.peek(None)
        if p is not None and predicate(p):
            yield next(iterable)
        else:
            break

def tokenize_line(line):
    char_iter = peekable(enumerate(line))
    line_tokens = []
    line_number = 0

    while char_iter.peek(None) is not None:
        pos, ch = next(char_iter)

        if pos == 0:
            if ch.isnumeric():
                num_chars = [x for (_, x) in itertools.takewhile(lambda x: not x[1].isspace(), char_iter)]
                try:
                    line_number = int("".join([ch] + num_chars))
                except ValueError:
                    raise Exception("Line must start with a line number followed by whitespace:\n\t{}" % line)
            else:
                raise Exception("Line must start with a line number followed by whitespace:\n\t{}" % line)
        else:
            if ch.isspace():
                # Skip whitespace
                continue

            # At the beginning of a string
            if ch == '"':
                str_chars = [x for (_, x) in itertools.takewhile(lambda x: x[1] != '"', char_iter)]
                bstring = "".join(str_chars)
                line_tokens.append(TokenAndPos(Token.BString(bstring), pos))
            elif ch == '-':
                # If the previous token is a value, it's a binary operation
                if is_value(line_tokens[-1].token):
                    line_tokens.append(TokenAndPos(Token.Minus(), pos))
                # Otherwise, unary minus
                else:
                    line_tokens.append(TokenAndPos(Token.UMinus(), pos))
            elif ch == '!':
                line_tokens.append(TokenAndPos(Token.Bang(), pos))
            elif ch == "(":
                line_tokens.append(TokenAndPos(Token.LParen(), pos))
            elif ch == ")":
                line_tokens.append(TokenAndPos(Token.RParen(), pos))
            else:
                token_chars = [x for (_, x) in _takewhile_peek(lambda x: not (x[1].isspace() or x[1] == ')'), char_iter)]
                token_chars.insert(0, ch)
                token_str = "".join(token_chars)

                if _is_int(token_str):
                    line_tokens.append(TokenAndPos(Token.Number(int(token_str)), pos))
                else:
                    token = get_token_for_string(token_str)

                    if token is None:
                        if _is_valid_identifier(token_str):
                            line_tokens.append(TokenAndPos(Token.Variable(name=token_str), pos))
                        else:
                            raise Exception("Unimplemented token at {}:\t{}".format(pos, token_str))
                    elif token == Token.Rem:
                        line_tokens.append(TokenAndPos(token(), pos))
                        comment_str = "".join(x[1] for x in char_iter)
                        line_tokens.append(TokenAndPos(Token.Comment(comment=comment_str), pos + 4))
                    else:
                        # Handle tokens that don't have things following
                        line_tokens.append(TokenAndPos(token(), pos))

    return LineOfCode(line_number, line_tokens)
