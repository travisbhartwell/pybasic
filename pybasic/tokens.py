import attr
from sumtypes import sumtype, constructor, match

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

    # // Operators
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
    Bang = constructor()

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
