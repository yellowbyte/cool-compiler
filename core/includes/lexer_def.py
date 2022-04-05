from enum import Enum
from collections import namedtuple


Token = namedtuple("Token", ["type", "val", "name"])

KNOWN_TOKENS = {
    # reserved words
    "procedure":1,
    "function":2,
    "return":3,
    "while":4,
    "let":5,
    "call":6,
    "array":7,
    "then":8,
    "else":9,
    "var":10,
    "if":11,
    "fi":12,
    "do":13,
    "od":14,
    # relational operator
    "<=":15,
    ">=":16,
    "==":17,
    "!=":18,
    "<":19,
    ">":20,
    # math
    "*":21,
    "/":22,
    "+":23,
    "-":24,
    # assignment 
    "<-":25,
    # separator
    ";":26,
    ",":27,
    ".":28,
    "(":29,
    ")":30,
    "{":31,
    "}":32,
    # predefined functions
    "OutputNewLine":33,
    "InputNum":34,
    "OutputNum":35,
} 

CUR_TOKEN_VAL = 36

LOOKAHEAD_TOKEN = None

TOKENIZER = None 

# possible token types
class TYPE(Enum):
    NUMBER = 1
    IDENTIFIER = 2
    RESERVED = 3
    OPERATOR = 4
    SEPARATOR = 5
    PREDEFINED = 6
    PARANS = 7
    MATH = 8



