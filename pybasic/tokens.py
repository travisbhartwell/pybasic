from enum import Enum

import attr
from sumtypes import sumtype, constructor, match_partial


@sumtype
class Token(object):
    Comment = constructor(
        comment=attr.ib(validator=attr.validators.instance_of(str)))

    # Variables and Literals
    Variable = constructor(
        name=attr.ib(validator=attr.validators.instance_of(str)))
    Number = constructor(
        value=attr.ib(validator=attr.validators.instance_of(int)))
    BString = constructor(
        value=attr.ib(validator=attr.validators.instance_of(str)))

    # Unary operators
    UMinus = constructor()
    Bang = constructor()

    # Operators
    Equals = constructor()
    LessThan = constructor()
    GreaterThan = constructor()
    LessThanEqual = constructor()
    GreaterThanEqual = constructor()
    NotEqual = constructor()
    Multiply = constructor()
    Divide = constructor()
    Minus = constructor()
    Plus = constructor()
    LParen = constructor()
    RParen = constructor()

    # Keywords
    Goto = constructor()
    If = constructor()
    Input = constructor()
    Let = constructor()
    Print = constructor()
    Rem = constructor()
    Then = constructor()


_str_to_token_map = {
    "=": Token.Equals,
    "<": Token.LessThan,
    ">": Token.GreaterThan,
    "<=": Token.LessThanEqual,
    ">=": Token.GreaterThanEqual,
    "<>": Token.NotEqual,
    "*": Token.Multiply,
    "/": Token.Divide,
    "-": Token.Minus,
    "+": Token.Plus,
    "(": Token.LParen,
    ")": Token.RParen,
    "!": Token.Bang,
    "GOTO": Token.Goto,
    "IF": Token.If,
    "INPUT": Token.Input,
    "LET": Token.Let,
    "PRINT": Token.Print,
    "REM": Token.Rem,
    "THEN": Token.Then
}

_token_to_str_map = {v: k for k, v in _str_to_token_map.items()}


def get_token_for_string(token_str):
    return _str_to_token_map.get(token_str, None)


def get_string_for_token(token_obj):
    return _token_to_str_map.get(type(token_obj), None)


def is_operator(token_obj):
    return isinstance(token_obj,
                      (Token.Equals, Token.LessThan, Token.GreaterThan, Token.LessThanEqual,
                       Token.NotEqual, Token.Multiply, Token.Divide, Token.Minus, Token.Plus,
                       Token.Bang, Token.UMinus))


def is_unary_operator(token_obj):
    return isinstance(token_obj,
                      (Token.UMinus, Token.Bang))


def is_value(token_obj):
    return isinstance(token_obj,
                      (Token.Variable, Token.Number, Token.BString))


class Associativity(Enum):
    Left = 0
    Right = 1


def get_operator_precedence(token_obj):
    if not is_operator(token_obj):
        raise Exception("Not an operator: {}".format(str(token_obj)))

    if isinstance(token_obj, (Token.UMinus, Token.Bang)):
        return 12
    elif isinstance(token_obj, (Token.Multiply, Token.Divide)):
        return 10
    elif isinstance(token_obj, (Token.Minus, Token.Plus)):
        return 8
    else:
        return 4


def get_operator_associativity(token_obj):
    if not is_operator(token_obj):
        raise Exception("Not an operator: {}".format(str(token_obj)))

    if isinstance(token_obj, (Token.UMinus, Token.Bang)):
        return Associativity.Right
    else:
        return Associativity.Left


@match_partial(Token)
class get_operation(object):
    def Equals():
        return lambda a, b: a == b

    def LessThan():
        return lambda a, b: a < b

    def GreaterThan():
        return lambda a, b: a > b

    def LessThanEqual():
        return lambda a, b: a <= b

    def NotEqual():
        return lambda a, b: a != b

    def Multiply():
        return lambda a, b: a * b

    def Divide():
        return lambda a, b: a / b

    def Minus():
        return lambda a, b: a - b

    def Plus():
        return lambda a, b: a + b

    def UMinus():
        return lambda a: -a

    def Bang():
        return lambda a: not a

    def _():
        raise NotImplementedError("Should not get here")
