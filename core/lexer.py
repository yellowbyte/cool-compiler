from .includes.lexer_def import *

from .helpers.logger import *

from .includes import lexer_def
from .includes import config


def get_token_name(val):
    """
    Get the name corresponding to the val (i.e., inverse of KNOWN_TOKENS)
    """
    return {v: k for k,v in KNOWN_TOKENS.items()}[val]

def get_token_val(name):
    """ 
    Get the val corresponding to name (i.e., reserved, identifier, etc) 
    """
    if name in KNOWN_TOKENS:
        return KNOWN_TOKENS[name]

    # new token
    KNOWN_TOKENS[name] = lexer_def.CUR_TOKEN_VAL
    lexer_def.CUR_TOKEN_VAL += 1
    return KNOWN_TOKENS[name]

def get_token():
    """A wrapper around `lexer` to get a lookahead token"""
    # essentially a generator wrapper around a generator so
    # not the best design choice but choice is made because
    # I realized late in the project that I needed a 
    # LOOKAHEAD_TOKEN
    f = config.FILE 
    lexer_def.TOKENIZER = lexer(f)
    config.LOOKAHEAD_TOKEN = next(lexer_def.TOKENIZER)
    cur_token = config.LOOKAHEAD_TOKEN
    config.LOOKAHEAD_TOKEN = next(lexer_def.TOKENIZER)
    yield cur_token

    while True: 
        cur_token = config.LOOKAHEAD_TOKEN
        try:
            config.LOOKAHEAD_TOKEN = next(lexer_def.TOKENIZER)
        except:
            pass
        yield cur_token

def lexer(reader):
    acc = str()  # accumulate the token
    _type = None
    val = 0

    char = reader.read(1)
    while True: 
        if not char:
            # finished tokenizing
            break

        # NUMBER
        if char.isdigit(): 
            acc += char
            char = reader.read(1)
            while (char.isdigit()):
                acc += char
                char = reader.read(1)
            _type = TYPE.NUMBER
            val = int(acc)
            acc = str()
            logging.debug(f"({_type}, {val}, {val})")
            yield Token(_type, val, val)

        # IDENTIFIER or RESERVED
        if char.isalpha():
            acc += char
            char = reader.read(1)
            while (char.isalnum()):
                acc += char
                char = reader.read(1)
            val = get_token_val(acc)
            acc = str()
            if val <= 14: 
                _type = TYPE.RESERVED
            elif val in [33,34,35]:
                if val == 33: 
                    # predefined function: InputNum()
# function can be called with our without paranthesis
#                    char = reader.read(1)  # remove '('
#                    char = reader.read(1)  # remove ')'
                    pass
                elif val == 35:
                    # predefined function: OutputNewLine()
# function can be called with our without paranthesis
#                    char = reader.read(1)  # remove '('
#                    char = reader.read(1)  # remove ')'
                    pass
                else:  # val == 34
                    # predefined function: OutputNum(x)
                    # the '(' and ')' need to be processed by
                    # parser since x can be an expression and
                    # that need to be processed by the parser
                    pass
                _type = TYPE.PREDEFINED
            else: 
                _type = TYPE.IDENTIFIER
            logging.debug(f"({_type}, {val}, {get_token_name(val)})")
            yield Token(_type, val, get_token_name(val))

        # RELATIONAL OPERATOR
        if char in ['=', '!', '<', '>']:
            acc += char 
            char = reader.read(1)
            # ==, !=, <=, >=
            if char == '=':
                acc += char
                char = reader.read(1)
            # assignment
            # <-
            if char == '-' and acc == '<':
                acc += char 
                char = reader.read(1)
            _type = TYPE.OPERATOR
            val = get_token_val(acc)
            acc = str()
            logging.debug(f"({_type}, {val}, {get_token_name(val)})")
            yield Token(_type, val, get_token_name(val))

        # MATH
        if char in ['+', '-', '*', '/']:
            acc += char
            char = reader.read(1)
            _type = TYPE.MATH
            val = get_token_val(acc)
            acc = str()
            logging.debug(f"({_type}, {val}, {get_token_name(val)})")
            yield Token(_type, val, get_token_name(val))

        # SEPARATOR
        if char in [';', ',', '.', '[', ']', '{', '}']:
            acc += char
            char = reader.read(1)
            _type = TYPE.SEPARATOR
            val = get_token_val(acc)
            acc = str()
            logging.debug(f"({_type}, {val}, {get_token_name(val)})")
            yield Token(_type, val, get_token_name(val))

        # PARANS
        if char in ['(', ')']:
            acc += char
            char = reader.read(1)
            _type = TYPE.PARANS
            val = get_token_val(acc)
            acc = str()
            logging.debug(f"({_type}, {val}, {get_token_name(val)})")
            yield Token(_type, val, get_token_name(val))

        if char.isspace():
            char = reader.read(1)
