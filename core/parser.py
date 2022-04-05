from .includes import config
from .includes import lexer_def

from .helpers.aux import *
from .helpers.logger import *

from .lexer import *
from .visualize import *


from pprint import pprint


def Parser(f):

    try: 
        # initialize TOKENIZER
        config.FILE = f
        config.TOKENIZER = get_token()
        # compute.
        computation()
    except Exception as e:
        logging.info("> ERROR")
        logging.info("error message: ")
        logging.info(e)


@recursion_tracker
def number():

    var = config.TOKEN.val
    sinstr = config.SInstr(f"const {var}", "")
    if not subexpression_search(0, sinstr):  # 0 for BB0
        # constant does not exist previously
        sval = config.CUR_SSA_VAL  
        # create SSA instruction and add it to basic block 0
        # constant becomes its own SSA value
        config.BB0.append( config.CODEinfo(0, config.CUR_SSA_VAL, sinstr) )  # 0 for BB0
        # constant do not exist in eventual code
        # linkedlist of same opcode        
        config.COMMON_SEARCH[0]["const"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )  # 0 for BB0
        config.CUR_SSA_VAL += 1
    else: 
        # constant exists previously
        sval = subexpression_search(0, sinstr)

    return (var,sval)


@recursion_tracker
def ident():
 
    var = config.TOKEN.val
    # if it is the beginning and variable never initialized, 
    # keep track of variable and initialize to 0
    if config.IN_FUNC_DECL:  # varDecl by main
        sinstr = config.SInstr("const 0", config.CONST0_VAR)
        # get the sval that corresponds to constant 0
        zero_sval = subexpression_search(0, sinstr)
        config.VARS_ASSIGN[config.CUR_BB.bval][var] = zero_sval  # 1 for first BB
    
    return var


@recursion_tracker
def designator():
 
    identifier = ident()

    config.ID_IS_ARRAY = False

    # array access 
    # need to add code for calculating FP + base (base is in `config.VARS_ASSIGN`)
    # calculate offsets first before multiplying by current index (this way common subexpression elimination works better)
    # EX: 
    # 3D array:
    #    (a * nb * nc * 4) + (b * nc * 4) + (c * 4)
    # calculate first: nc * 4
    # calculate second: nb * nc * 4
    # calculate third: a* nb * nc * 4
    # this way there is no redundent nc * 4
    # for higher dimensions, there will be more subexpressions eliminated
    i = 0  # inner array dims starting offset
    offsets_sval = list()
    to_add_sval = list()
    dims = list()
    while (config.LOOKAHEAD_TOKEN.val == get_token_val('[')):

        # it is an array
        config.ID_IS_ARRAY = True 

        # consume identifier or "]"
        config.TOKEN = next(config.TOKENIZER)
        # consume "["
        config.TOKEN = next(config.TOKENIZER)

        if i == 0:
            # perform array base address calculation
            sinstr = config.SInstr(f"add FP {config.VARS_ASSIGN[config.CUR_BB.bval][identifier]}", "", identifier)
            base_sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not base_sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["add"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                base_sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
            # perform partial offset calculation
            dims = config.ARRAY_DIMS[identifier]
            sval = None  # will be assigned soonish..

            if len(dims) > 1:
                ind = 0
                for d_const,d_sval in reversed(dims[1:]):
                    d_const_sval = subexpression_search(config.CUR_BB.bval, config.SInstr(f"const {d_const}", ""))

                    if ind == 0:
                        const4_sval = subexpression_search(config.CUR_BB.bval, config.SInstr(f"const 4", ""))
                        sinstr = config.SInstr(f"mul {d_const_sval} {const4_sval}", d_const, "")
                    else:
                        sinstr = config.SInstr(f"mul {d_const_sval} {sval}", d_const, "")

                    sval = subexpression_search(config.CUR_BB.bval, sinstr)
                    if not sval:
                        # common subexpression not found
                        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                        config.COMMON_SEARCH[config.CUR_BB.bval]["mul"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                        sval = config.CUR_SSA_VAL
                        config.CUR_SSA_VAL += 1
                    offsets_sval.insert(0,sval)

                    # update loop index
                    ind += 1

        # get effective array offsets
        var,sval = expression()
        config.ID_IS_ARRAY = True 

        # calculate effective offset for current dimension        
        # multiply current index with current offset
        if i != len(dims)-1:
            # not the last dimension
            sinstr = config.SInstr(f"mul {sval} {offsets_sval[i]}", var, "")
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["mul"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
        else:
            # last dimension (just need to multiply `sval` by 4)
            const4_sval = subexpression_search(config.CUR_BB.bval, config.SInstr(f"const 4", ""))
            sinstr = config.SInstr(f"mul {sval} {const4_sval}", var, "")
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["mul"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
        to_add_sval.append(sval)

        # go to next index
        i += 1

    # not an array
    if not config.ID_IS_ARRAY:
        return identifier

    # generate adding offset
    if len(to_add_sval) > 1:
        sval = to_add_sval[0]
        for add_sval in to_add_sval[1:]:
            sinstr = config.SInstr(f"add {sval} {add_sval}", "", "")
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["add"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1

    # generate adding base addr with effective offset
    sinstr = config.SInstr(f"adda {sval} {base_sval}", "", "")
    sval = subexpression_search(config.CUR_BB.bval, sinstr)
    if not sval:
        # common subexpression not found
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
        config.COMMON_SEARCH[config.CUR_BB.bval]["adda"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
        sval = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1

    # return sval corresponding to the memory address
    return sval
        

@recursion_tracker
def statement():
 
    if config.TOKEN.val == get_token_val("let"):
        config.TOKEN = next(config.TOKENIZER)  # TOKEN is now the identifier token
        # 'assignment'
        assignment()
    elif config.TOKEN.val == get_token_val("call"):
        funcCall()
    elif config.TOKEN.val == get_token_val("return"):
        returnStatement()
    elif config.TOKEN.val == get_token_val("if"):
        ifStatement()
    elif config.TOKEN.val == get_token_val("while"):
        whileStatement()

    return None


@recursion_tracker
def statSequence():

    statement()
    while (config.TOKEN.val == get_token_val(';')):
        config.TOKEN = next(config.TOKENIZER)
        if config.TOKEN.val == get_token_val('}'):
            break
        statement()
    if config.TOKEN.val == get_token_val(';'):
        config.TOKEN = next(config.TOKENIZER)

    return None


@recursion_tracker
def typeDecl():
 
    _type = None
    if config.TOKEN.val == get_token_val("var"):
        _type = "var"
        # consume "var"
        config.TOKEN = next(config.TOKENIZER)

    if config.TOKEN.val == get_token_val("array"):
        _type = "array"
        # language only support int array
        # consume "array"
        config.TOKEN = next(config.TOKENIZER)
        # consume "["
        config.TOKEN = next(config.TOKENIZER)

        # array offsets
        config.CUR_OFFSETS = 0
        config.CUR_LIST = list()
        const,sval = number()  # will associate a sval with the constant if never seen before
        config.CUR_OFFSETS += int(const)
        config.CUR_LIST.append((const,sval))
        # consume "number"
        config.TOKEN = next(config.TOKENIZER)

        # consume "]"
        config.TOKEN = next(config.TOKENIZER)
        # multi-dimensional array
        while (config.TOKEN.val == get_token_val('[')):
            # consume "["
            config.TOKEN = next(config.TOKENIZER)

            const,_ = number()  # will associate a sval with the constant if never seen before
            # update `offsets` to account for multi-dimensions
            config.CUR_OFFSETS *= int(const)
            config.CUR_LIST.append((const,sval))
            # consume "number"
            config.TOKEN = next(config.TOKENIZER)

            # consume "]"
            config.TOKEN = next(config.TOKENIZER)

        # getting effective offsets (account for element size)
        config.CUR_OFFSETS *= 4

    return _type


@recursion_tracker
def varDecl():

    # consume "var" or "array"
    config.TOKEN = next(config.TOKENIZER)
   
    _type = typeDecl()

    var = ident()
    if _type == "array":
        config.VARS_ASSIGN[config.CUR_BB.bval][var] = config.GLOBAL_OFFSETS 
        config.GLOBAL_OFFSETS += config.CUR_OFFSETS
        config.ARRAY_DIMS[var] = config.CUR_LIST
    # consume "ident"
    config.TOKEN = next(config.TOKENIZER)
    
    while(config.TOKEN.val == get_token_val(',')):
        # consume ','
        config.TOKEN = next(config.TOKENIZER)
        var = ident()
        if _type == "array":
            # sval for arrays are their offsets from FP
            config.VARS_ASSIGN[config.CUR_BB.bval][var] = config.GLOBAL_OFFSETS 
            config.GLOBAL_OFFSETS += config.CUR_OFFSETS
            config.ARRAY_DIMS[var] = config.CUR_LIST
        # consume "ident"
        config.TOKEN = next(config.TOKENIZER)

    return None


@recursion_tracker
def formalParam():

    # consume "("
    config.TOKEN = next(config.TOKENIZER)

    if (config.LOOKAHEAD_TOKEN.val != get_token_val(")")):
        # consume token representing ident
        config.TOKEN = next(config.TOKENIZER)
        var = ident()
        # parameters become svals in the beginning of the basic block
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr(f"param {var}", "")) )
        config.VARS_ASSIGN[config.CUR_BB.bval][var] = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1
        # consume ")"
        config.TOKEN = next(config.TOKENIZER)
        while(config.TOKEN.val == get_token_val(",")):
            # consume ","
            config.TOKEN = next(config.TOKENIZER)
            var = ident()
            # parameters become svals in the beginning of the basic block
            config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr(f"param {var}", "")) )
            config.VARS_ASSIGN[config.CUR_BB.bval][var] = config.CUR_SSA_VAL
            config.CUR_SSA_VAL += 1
            # consume ")"
            config.TOKEN = next(config.TOKENIZER)
    else:
        # consume ")"
        config.TOKEN = next(config.TOKENIZER)


@recursion_tracker
def funcBody():

    config.IN_FUNC_DECL = True
    while( (config.LOOKAHEAD_TOKEN.val == get_token_val("var")) or (config.LOOKAHEAD_TOKEN.val == get_token_val("array")) ):
        varDecl()
    config.IN_FUNC_DECL = False

    # consume '{'
    config.TOKEN = next(config.TOKENIZER)

    if config.LOOKAHEAD_TOKEN.val != get_token_val("}"):
        # consume token for beginning of sequence
        config.TOKEN = next(config.TOKENIZER)
        statSequence()
        
    # add RET
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("ret")) )
    config.CUR_SSA_VAL += 1


@recursion_tracker
def funcDecl():

    config.CUR_BB = create_bb("bb1", 0) 
    if (config.LOOKAHEAD_TOKEN.val == get_token_val("void")):
        # consume "void"
        config.TOKEN = next(config.TOKENIZER)
    # consume "function"
    config.TOKEN = next(config.TOKENIZER)

    # save location (sval) of where function begins
    # consume ident
    config.TOKEN = next(config.TOKENIZER)
    var = ident()
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("")) )
    # first element is starting index, second element is ending index (in sval)
    # get second element later
    config.FUNCTIONS[var] = [config.CUR_SSA_VAL]
    config.CUR_SSA_VAL += 1

    # when CALL is encountered:
    #   pass svals of the params in one call
    #   EX: call var, sval1, sval2, sval3
    #       where it is defined as call func1(arg1, arg2, arg3)

    formalParam()

    # consume ";"
    config.TOKEN = next(config.TOKENIZER)

    funcBody()

    # consume ";"
    config.TOKEN = next(config.TOKENIZER)
    delete_bb(config.CUR_BB, "bb1")

    # get second element (ending index)
    config.FUNCTIONS[var].append(config.CODE[-1].sval)
 

@recursion_tracker
def computation():

    # add constant 0
    sinstr = config.SInstr("const 0", lexer_def.CUR_TOKEN_VAL)
    config.CONST0_VAR = lexer_def.CUR_TOKEN_VAL
    lexer_def.CUR_TOKEN_VAL += 1
    config.BB0.append( config.CODEinfo(0, config.CUR_SSA_VAL, sinstr) )  # 0 for BB0
    config.COMMON_SEARCH[0]["const"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )  # 0 for BB0
    config.CUR_SSA_VAL += 1
    # add constant 4 (for calculating array offset)
    sinstr = config.SInstr("const 4", lexer_def.CUR_TOKEN_VAL)
    config.CONST4_VAR = lexer_def.CUR_TOKEN_VAL
    lexer_def.CUR_TOKEN_VAL += 1
    config.BB0.append( config.CODEinfo(0, config.CUR_SSA_VAL, sinstr) )  # 0 for BB0
    config.COMMON_SEARCH[0]["const"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )  # 0 for BB0
    config.CUR_SSA_VAL += 1

    config.CUR_BB = create_bb("bb1", 0) 

    # consume "main"
    config.TOKEN = next(config.TOKENIZER)
    var = ident()  # var token value corresponding to main
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("")) )
    # first element is starting index, second element is ending index (in sval)
    # get second element later
    config.FUNCTIONS[var] = [config.CUR_SSA_VAL]
    config.CUR_SSA_VAL += 1

    config.IN_FUNC_DECL = True
    while( (config.LOOKAHEAD_TOKEN.val == get_token_val("var")) or (config.LOOKAHEAD_TOKEN.val == get_token_val("array")) ):
        varDecl()
    config.IN_FUNC_DECL = False

    while( (config.LOOKAHEAD_TOKEN.val == get_token_val("void")) or (config.LOOKAHEAD_TOKEN.val == get_token_val("function")) ):
        funcDecl()

    # consume '{'
    config.TOKEN = next(config.TOKENIZER)

    # consume first token of sequence
    config.TOKEN = next(config.TOKENIZER)
    statSequence()

    # consume '.'
    config.TOKEN = next(config.TOKENIZER)

    # program done. 
    sinstr = config.SInstr("end")
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )

    delete_bb(config.CUR_BB, "bb1")

    # get second element (ending index)
    config.FUNCTIONS[var].append(config.CODE[-1].sval)
 
    return None


@recursion_tracker
def assignment():
    config.IS_ARRAY_INSTR = False
    # 'let' already consumed
    # TOKEN is the identifier/var
    var = designator()
    if config.ID_IS_ARRAY:
        config.IS_ARRAY_INSTR = True

    # consume "<-"
    config.TOKEN = next(config.TOKENIZER)

    # get expression token
    # (first token of the expression)
    config.TOKEN = next(config.TOKENIZER)

    _,sval = expression()

    # table update 
    if config.IS_ARRAY_INSTR:
        sinstr = config.SInstr(f"store {sval} {var}", "", "")
        sval = subexpression_search(config.CUR_BB.bval, sinstr)
        if not sval:
            # common subexpression not found
            config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
            config.COMMON_SEARCH[config.CUR_BB.bval]["load"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
            sval = config.CUR_SSA_VAL
            config.CUR_SSA_VAL += 1
        if config.INSIDE_LOOP:
            config.ADD_KILL = True
    else:
        config.VARS_ASSIGN[config.CUR_BB.bval][var] = sval

    return None


@recursion_tracker
def expression():

    var,sval = term()

    while (config.TOKEN.val == get_token_val('+') or config.TOKEN.val == get_token_val('-')):
        if config.TOKEN.val == get_token_val('+'):
            config.TOKEN = next(config.TOKENIZER)
            rvar,rsval = term()
            sinstr = config.SInstr(f"add {sval} {rsval}", var, rvar)
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["add"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
        else:  # subtraction
            config.TOKEN = next(config.TOKENIZER)
            rvar,rsval = term()
            sinstr = config.SInstr(f"sub {sval} {rsval}", var, rvar)
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["sub"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1

    return (var,sval)


@recursion_tracker
def term():

    var,sval = factor()

    while (config.TOKEN.val == get_token_val('*') or config.TOKEN.val == get_token_val('/')):
        if config.TOKEN.val == get_token_val('*'):
            config.TOKEN = next(config.TOKENIZER)
            rvar,rsval = factor()
            sinstr = config.SInstr(f"mul {sval} {rsval}", var, rvar)
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["mul"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
        else:  # division
            config.TOKEN = next(config.TOKENIZER)
            rvar,rsval = factor()
            sinstr = config.SInstr(f"div {sval} {rsval}", var, rvar)
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["div"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1

    return (var,sval)


@recursion_tracker
def factor():

    sval = None
    var = None

    if config.TOKEN.type == TYPE.NUMBER:    
        # number
        var,sval = number()
        config.TOKEN = next(config.TOKENIZER)
    elif config.TOKEN.type == TYPE.IDENTIFIER: 
        # designator
        var = designator()
        if config.ID_IS_ARRAY:
            sinstr = config.SInstr(f"load {var}", "")
            sval = subexpression_search(config.CUR_BB.bval, sinstr)
            if not sval:
                # common subexpression not found
                config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
                config.COMMON_SEARCH[config.CUR_BB.bval]["load"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
                sval = config.CUR_SSA_VAL
                config.CUR_SSA_VAL += 1
        else:
            sval = config.VARS_ASSIGN[config.CUR_BB.bval][var]
        config.TOKEN = next(config.TOKENIZER)
    elif config.TOKEN.type == TYPE.PARANS: 
        # "(" expression ")"
        config.TOKEN = next(config.TOKENIZER)  # '('
        var,sval = expression()
        config.TOKEN = next(config.TOKENIZER)  # ')'
    else:  # function call
        var,sval = funcCall()

    return (var,sval)


def relation():

    lvar,lsval = expression()

    # consume relOP 
    relOP = config.TOKEN    
    config.TOKEN = next(config.TOKENIZER)  # move pass relOP
    rvar,rsval = expression()

    # if-statement breaks down into 2 instructions 
    # (1) subtraction
    sinstr = config.SInstr(f"sub {lsval} {rsval}", lvar, rvar)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
    config.COMMON_SEARCH[config.CUR_BB.bval]["sub"].insert(0, config.Sinfo(config.CUR_SSA_VAL,sinstr) )
    xsval = config.CUR_SSA_VAL  # value conditional branch instruction is based on 
    config.CUR_SSA_VAL += 1
    sval = config.CUR_SSA_VAL  # ssa value of the conditional branch instruction 
    config.CUR_SSA_VAL += 1
    # (2) branch instruction
    # opposite of the source conditional branch 
    # (this way then block will follow the branch block and the branch will branch to else block)
    if relOP.val == get_token_val("=="):
        sinstr = config.SInstr(f"bne {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
    elif relOP.val == get_token_val("!="):
        sinstr = config.SInstr(f"beq {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
    elif relOP.val == get_token_val("<"):
        sinstr = config.SInstr(f"bge {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
    elif relOP.val == get_token_val("<="):
        sinstr = config.SInstr(f"bgt {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
    elif relOP.val == get_token_val(">"):
        sinstr = config.SInstr(f"ble {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
    elif relOP.val == get_token_val(">="):
        sinstr = config.SInstr(f"blt {xsval} {config.CUR_SSA_VAL}", "","")
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, sval, sinstr) )
#    config.CUR_SSA_VAL += 1  # for if-statement, the first instruction in else block will use this ssa value
                              # for while-statement, the first instruction of the follow block will use this

    return None


@recursion_tracker
def whileStatement():
    # create join block
    og_bval = config.CUR_BB.bval
    og_edge_sval = delete_bb(config.CUR_BB, "bb1")
    ###config.CUR_BB = create_bb("bb1", config.CUR_BB.bval)
    config.CUR_BB = create_bb("bb1", og_bval)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("")) )
    join_bval = config.CUR_BB.bval
    join_sval = config.CUR_SSA_VAL
    config.CUR_SSA_VAL += 1
    # keep track of the join block
    config.PREV_BB = config.CUR_BB

    # consume "while"
    config.TOKEN = next(config.TOKENIZER)  # "while"

    relation()

    # sval of first sinstr in follow
    # to add `follow_sval` to immediate basic block that follows the loop exit
    follow_sval = config.CUR_SSA_VAL
    config.CUR_SSA_VAL += 1

    # add join block
    join_bval = config.CUR_BB.bval
    og_edge_sval = delete_bb(config.CUR_BB, "bb1")
    follow_bval = config.CUR_BB.bval

    # create another CUR_BB for loop body
    # loop body basic block will follow the join basic block
    ###config.CUR_BB = create_bb("bb1", config.CUR_BB.bval)
    config.CUR_BB = create_bb("bb1", join_bval)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("")) )
    config.CUR_SSA_VAL += 1

    # consume "do"
    config.TOKEN = next(config.TOKENIZER)  # "do"

    pre_deleted_bbs = set(get_deleted_bbs())
    statSequence()

    # consume "od"
    config.TOKEN = next(config.TOKENIZER)  # "od"

    # add 'bra' to end of `config.CUR_BB` (loop body)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr(f"bra {join_sval}", "")) )
    config.CUR_SSA_VAL += 1

    # find changed/new variables in `config.CUR_BB` compared to old `config.CUR_BB` (`og_bval`)
    og_vars_table = config.VARS_ASSIGN[og_bval]
    cur_vars_table = config.VARS_ASSIGN[config.CUR_BB.bval]
    changed_vars = {k: cur_vars_table[k] for k in cur_vars_table.keys() if k not in og_vars_table.keys() or cur_vars_table[k] != og_vars_table[k]}
    # add last basic block in loop body to eventual code
    body_edge_sval = delete_bb(config.CUR_BB, "bb1")

    # basic blocks that are deleted since
    # we need to propagate the new phi's to every basic blocks in `bb2update`
    post_deleted_bbs = set(get_deleted_bbs())
    bb2update = post_deleted_bbs - pre_deleted_bbs

    # keep track of where to add phi's in the eventual code 
    phi_index = config.SVAL2INDEX[join_sval] + 1
    # var -> (old sval,new sval) mapping for propagating phi's sval
    updated_var2sval = dict()
    # create phi's from them and add to basic block corresponding to join block (`config.CUR_BB`)
    for var,sval in changed_vars.items():
        og_sval = og_vars_table[var]
        sinstr = config.SInstr(f"phi {og_sval} {sval}", "", "")
        config.CODE.insert(phi_index, config.CODEinfo(join_bval, config.CUR_SSA_VAL, sinstr) )  # 0, beginning is reserved for the entrance, empty sval
        updated_var2sval[var] = (og_sval,config.CUR_SSA_VAL)
        # update `VARS_ASSIGN` for downstream
        config.VARS_ASSIGN[join_bval][var] = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1

    # update `SVAL2INDEX` since while-statement messed it up by adding phi's
    config.SVAL2INDEX = dict()
    for i,ci in enumerate(config.CODE):
        config.SVAL2INDEX[ci.sval] = i

    # propagate the changes to the current join block (i.e., all svals that are not part of a phi)

    # propagate the changes to `bb2update` + `config.PREV_BB`
    # only have to change the sinstrs
    bb2update = list(bb2update)
    for ci in config.CODE:
        if ci.bval in bb2update:
            # this basic block may needs to be updated
            if ci.sinstr.lvar:  # left operand exists
                if ci.sinstr.lvar in updated_var2sval.keys() and int(ci.sinstr.lsval) == updated_var2sval[ci.sinstr.lvar][0]:
                    ci.sinstr.lsval = str(updated_var2sval[ci.sinstr.lvar][1])
            if ci.sinstr.rvar:  # right operand exists 
                if ci.sinstr.rvar in updated_var2sval.keys() and int(ci.sinstr.rsval) == updated_var2sval[ci.sinstr.rvar][0]:
                    ci.sinstr.rsval = str(updated_var2sval[ci.sinstr.rvar][1])
        if ci.bval == join_bval: 
            # the join block may also need updates 
            if ci.sinstr.opcode == "phi":
                continue
            # this basic block may needs to be updated
            if ci.sinstr.lvar:  # left operand exists
                if ci.sinstr.lvar in updated_var2sval.keys() and int(ci.sinstr.lsval) == updated_var2sval[ci.sinstr.lvar][0]:
                    ci.sinstr.lsval = str(updated_var2sval[ci.sinstr.lvar][1])
            if ci.sinstr.rvar:  # right operand exists 
                if ci.sinstr.rvar in updated_var2sval.keys() and int(ci.sinstr.rsval) == updated_var2sval[ci.sinstr.rvar][0]:
                    ci.sinstr.rsval = str(updated_var2sval[ci.sinstr.rvar][1])

    # follow block 
    config.CUR_BB = create_bb("bb1", join_bval)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, follow_sval, config.SInstr("")) )

    return None


@recursion_tracker
def ifStatement():

    # create join block
    origin_bval = config.CUR_BB.bval
    config.OTHER_BB = create_bb("bb2", config.CUR_BB.bval)
    # create empty sval for first sinstr of join block
    # keep track of join block's first sval since then block needs to branch there
    join_sval = config.CUR_SSA_VAL
    config.OTHER_BB.storage.append( config.CODEinfo(config.OTHER_BB.bval, join_sval, config.SInstr("")) )
    config.CUR_SSA_VAL += 1

    # consume "if"
    config.TOKEN = next(config.TOKENIZER)  # "if"

    relation()

    # current `CUR_SSA_VAL` is for the first instruction in the else block
    # save it and use it if else block is created
    else_sval = config.CUR_SSA_VAL
    config.CUR_SSA_VAL += 1

    # add current basic block to eventual code
    # needs to create then/else blocks
    branch_bval = config.CUR_BB.bval  # use this to index `VARS_ASSIGN`
    edge_sval = delete_bb(config.CUR_BB, "bb1")

    # consume "then"
    config.TOKEN = next(config.TOKENIZER)  # "then"

    # then block
    config.CUR_BB = create_bb("bb1", origin_bval)
    # add an empty ssa value in beginning 
    # (if basic block ends up to be empty, we still need the basic block to exist)
    config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr("")) )
    config.CUR_SSA_VAL += 1

    config.INSIDE_LOOP = True
    statSequence()
    config.INSIDE_LOOP = False
    if config.ADD_KILL:
        config.OTHER_BB.storage.insert(1, config.CODEinfo(config.OTHER_BB.bval, config.CUR_SSA_VAL, config.SInstr("kill")) )
        config.CUR_SSA_VAL += 1
        config.ADD_KILL = False

    lbb_val = config.CUR_BB.bval
    ledge_sval = None
    rbb_val = None
    redge_sval = None    

    if (config.TOKEN.val == get_token_val("else")):
        # add bra instruction to go to join block (i.e., skip else block)
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr(f"bra {join_sval}", "")) )
        config.CUR_SSA_VAL += 1
        ledge_sval = delete_bb(config.CUR_BB, "bb1")

        # consume "else"
        config.TOKEN = next(config.TOKENIZER)  # "else"
        # else block        
        config.CUR_BB = create_bb("bb1", branch_bval)
        # add `else_sval` to the beginning 
        # (if basic block ends up to be empty, we still need the basic block to exist)
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, else_sval, config.SInstr("")) )

        config.INSIDE_LOOP = True
        statSequence()
        config.INSIDE_LOOP = False
        if config.ADD_KILL:
            config.OTHER_BB.storage.insert(1, config.CODEinfo(config.OTHER_BB.bval, config.CUR_SSA_VAL, config.SInstr("kill")) )
            config.CUR_SSA_VAL += 1
            config.ADD_KILL = False
       
        rbb_val = config.CUR_BB.bval
        redge_sval = delete_bb(config.CUR_BB, "bb1")
    else: 
        # add bra instruction to go to join block (i.e., skip else block)
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, config.SInstr(f"bra {else_sval}", "")) )
        config.CUR_SSA_VAL += 1
        ledge_sval = delete_bb(config.CUR_BB, "bb1")

        # if no else block
        # since end of then block branched to `else_sval`
        # add `else_sval` as first sval of join block
        config.OTHER_BB.storage.insert(0, config.CODEinfo(config.OTHER_BB.bval, else_sval, config.SInstr("")))

    # consume token after "fi": ;
    config.TOKEN = next(config.TOKENIZER)  # "fi"

    # update join block with phi's
    if rbb_val:
        # else block exists
        update_if_phi(config.OTHER_BB, branch_bval, [lbb_val, rbb_val])    
    else:
        # else block does not exists
        update_if_phi(config.OTHER_BB, branch_bval, [lbb_val])

    # add join block to eventual code
    join_bval = config.OTHER_BB.bval
    delete_bb(config.OTHER_BB, "bb2")

    # need a working `CUR_BB` since deleted previously
    config.CUR_BB = create_bb("bb1", join_bval, bb_val=join_bval)

    return None
    

@recursion_tracker
def funcCall():

    sval = None
    var = None
    call_sval = None

    # consume "call"
    config.TOKEN = next(config.TOKENIZER)  # "call"

    if config.TOKEN.type == TYPE.PREDEFINED:
        if config.TOKEN.val == get_token_val("InputNum"):
            sinstr = config.SInstr("read")
            config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
            call_sval = config.CUR_SSA_VAL
            # function call be called with/without paranthesis
            if (config.LOOKAHEAD_TOKEN.val == get_token_val('(')):
                # consume '('
                config.TOKEN = next(config.TOKENIZER)  
                # consume ')'
                config.TOKEN = next(config.TOKENIZER)  
                # consume ';'
                config.TOKEN = next(config.TOKENIZER)  
            else: 
                # consume ';'
                config.TOKEN = next(config.TOKENIZER)  
        elif config.TOKEN.val == get_token_val("OutputNewLine"):
            sinstr = config.SInstr("writeNL")
            config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
            call_sval = config.CUR_SSA_VAL
            # function call be called with/without paranthesis
            if (config.LOOKAHEAD_TOKEN.val == get_token_val('(')):
                # consume '('
                config.TOKEN = next(config.TOKENIZER)  
                # consume ')'
                config.TOKEN = next(config.TOKENIZER)  
        else:  # OutputNum(x)
            # consume '('
            config.TOKEN = next(config.TOKENIZER)  
            # get expression token
            # (first token of the expression)
            config.TOKEN = next(config.TOKENIZER)  
            var,sval = expression()            
            # consume ')'
            config.TOKEN = next(config.TOKENIZER)  
            sinstr = config.SInstr(f"write {sval}", var)
            config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
            call_sval = config.CUR_SSA_VAL

        sval = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1
    else:
        # user-defined function
        func_sval = config.FUNCTIONS[config.TOKEN.val][0] 
        func_args = list()
        func_arg_vars = list()
        if config.LOOKAHEAD_TOKEN.val == get_token_val('('):
            # consume '('
            config.TOKEN = next(config.TOKENIZER)  

            if config.LOOKAHEAD_TOKEN.val == get_token_val(')'):
                # consume ')'
                config.TOKEN = next(config.TOKENIZER)  
            else: 
                # function has arguments 
                # consume first token of expression/argument
                config.TOKEN = next(config.TOKENIZER)  

                var,sval = expression()
                func_args.append(f"{sval}")
                func_arg_vars.append(var)

                while config.TOKEN.val == get_token_val(','):
                    # consume ','
                    config.TOKEN = next(config.TOKENIZER)  
                    var,sval = expression()
                    func_args.append(f"{sval}")

                # consume ')'
                config.TOKEN = next(config.TOKENIZER)  
        else:
            # consume ident
            config.TOKEN = next(config.TOKENIZER)  

        args_str = " ".join(func_args)
        if func_args:
            sinstr = config.SInstr(f"call {func_sval} {args_str}", var, *func_arg_vars)
        else:
            sinstr = config.SInstr(f"call {func_sval}", var)
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
        call_sval = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1

    return ("",call_sval)


@recursion_tracker
def returnStatement():

    # consume "return"
    config.TOKEN = next(config.TOKENIZER)

    if (config.TOKEN.val == get_token_val(';')) or (config.TOKEN.val == get_token_val('}')):
        # no return value
        return
    else:
        # there is return value
        var,sval =  expression()
        # R0 will be the register that stores return value
        sinstr = config.SInstr(f"mu R0 {sval}", "", var)
        config.CUR_BB.storage.append( config.CODEinfo(config.CUR_BB.bval, config.CUR_SSA_VAL, sinstr) )
        config.CUR_SSA_VAL += 1
