from collections import namedtuple
import itertools

from .tokens import Token, get_token_for_string, is_value

from more_itertools import peekable


TokenAndPos = namedtuple('TokenAndPos', ['token', 'pos'])
LineOfCode = namedtuple('LineOfCode', ['line_number', 'tokens'])


def _is_int(number):
    try:
        int(number)
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

        if not all((c == '_' or c.isalnum()) for c in ident[1:]):
            return False

    return True


def _takewhile_peek(predicate, iterable):
    """
    Alternate implementation of itertools.takewhile() that uses peek.
    """
    while True:
        iter_next = iterable.peek(None)
        if iter_next is not None and predicate(iter_next):
            yield next(iterable)
        else:
            break


def _get_line_number(char_iter):
    if char_iter.peek(None) is not None:
        pos, char = next(char_iter)

        assert pos == 0, "Must look for line numbers at beginning of line"

        if char.isnumeric():
            num_chars = [
                x
                for (_, x) in itertools.takewhile(lambda x: not x[1].isspace(),
                                                  char_iter)
            ]
            try:
                return int("".join([char] + num_chars))
            except ValueError:
                # Didn't find a valid line number, so the default error case
                # applies
                pass

    raise Exception("Line must start with a valid line number followed by whitespace.")


def tokenize_line(line):
    char_iter = peekable(enumerate(line))
    line_tokens = []
    line_number = _get_line_number(char_iter)

    while char_iter.peek(None) is not None:
        pos, char = next(char_iter)

        # Skip Whitespace
        if char.isspace():
            continue

        # At the beginning of a string
        if char == '"':
            str_chars = [
                x
                for (_, x) in itertools.takewhile(lambda x: x[1] != '"',
                                                  char_iter)
            ]
            bstring = "".join(str_chars)
            line_tokens.append(TokenAndPos(Token.BString(bstring), pos))
        # Minus operator
        elif char == '-':
            # If the previous token is a value, it's a binary operation
            if is_value(line_tokens[-1].token):
                line_tokens.append(TokenAndPos(Token.Minus(), pos))
            # Otherwise, unary minus
            else:
                line_tokens.append(TokenAndPos(Token.UMinus(), pos))
        # Bang operator
        elif char == '!':
            line_tokens.append(TokenAndPos(Token.Bang(), pos))
        # Left Parenthesis
        elif char == "(":
            line_tokens.append(TokenAndPos(Token.LParen(), pos))
        # Right Parenthesis
        elif char == ")":
            line_tokens.append(TokenAndPos(Token.RParen(), pos))
        else:
            token_chars = [
                x
                for (_, x) in _takewhile_peek(
                    lambda x: not (x[1].isspace() or x[1] == ')'), char_iter)
            ]
            token_chars.insert(0, char)
            token_str = "".join(token_chars)

            if _is_int(token_str):
                line_tokens.append(
                    TokenAndPos(Token.Number(int(token_str)), pos))
            else:
                token = get_token_for_string(token_str)

                if token is None:
                    if _is_valid_identifier(token_str):
                        line_tokens.append(
                            TokenAndPos(
                                Token.Variable(name=token_str), pos))
                    else:
                        raise Exception("Unimplemented token at {}:\t{}".
                                        format(pos, token_str))
                elif token == Token.Rem:
                    line_tokens.append(TokenAndPos(token(), pos))
                    comment_str = "".join(x[1] for x in char_iter)
                    line_tokens.append(
                        TokenAndPos(
                            Token.Comment(comment=comment_str), pos + 4))
                else:
                    # Handle tokens that don't have things following
                    line_tokens.append(TokenAndPos(token(), pos))

    return LineOfCode(line_number, line_tokens)
