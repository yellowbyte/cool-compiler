from .includes import config

from .helpers.logger import *

from .lexer import get_token_val

from pprint import pprint



CONTROL_ALTERING_INSTRS = ["bne", "beq", "bge", "bgt", "ble", "blt", "bra"]


def sval2bval(sval):
    codeinfo = config.CODE[config.SVAL2INDEX[sval]]
    return codeinfo.bval


def create_graph_bb(bb_instrs, bval):
    template = "bb"+str(bval)+" [shape=record, label=\"<b>BB"+str(bval)+" | {" 
    template += "|".join(bb_instrs)
    template += "}\"];"
    return template


def vis(code, func):
    base = ["digraph G {"]

    # func var
    var = get_token_val(func)
    func_start, func_end = config.FUNCTIONS[var]

    fall_relations = set()  # list of tuple with fall-through relations
    branch_relations = set()  # list of tuple with branch relations

    is_fall_through = False  # fall-through from branching
    fall_through_parent = None

    # get function code only
    func_code = list()
    IN_RANGE = False
    for ci in code:
        if ci.sval == func_start: 
            IN_RANGE = True 
        if ci.sval == func_end: 
            # add last instruction in range
            func_code.append(ci)
            break

        if not IN_RANGE: 
            continue
        func_code.append(ci)


    # identify basic blocks
    prev_bval = func_code[0].bval
    bb_instrs = list()
    for ci in func_code:

        if ci.bval == prev_bval:
            # same basic block as previous instruction
            bb_instrs.append(str(ci.sval)+": "+str(ci.sinstr.full))
        else:
            # new basic block
            bb_layout = create_graph_bb(bb_instrs, prev_bval)
            base.append(bb_layout)
            bb_instrs = list()
            bb_instrs.append(str(ci.sval)+": "+str(ci.sinstr.full))

        prev_bval = ci.bval

    # create last bb
    # create bb component in graph
    bb_layout = create_graph_bb(bb_instrs, func_code[-1].bval)
    base.append(bb_layout)
        
    # identify relations
    prev_bval = func_code[0].bval
    prev_is_bra = False
    bb_instrs = list()
    for ci in func_code: 

        opcode = ci.sinstr.opcode
        if opcode not in CONTROL_ALTERING_INSTRS:
            # not a branch-related instruction

            # check if it is an implicit branch
            # ex: nested join fall-through to the outermost join
            if prev_bval != ci.bval and not is_fall_through and not prev_is_bra:
                fall_relations.add( (prev_bval,ci.bval) )

            if prev_bval != ci.bval and is_fall_through:
                # create bb component in graph
                fall_relations.add( (prev_bval,ci.bval) )

            # check if previous `ci` is a branch-related instruction
            if is_fall_through:
                is_fall_through = False

            prev_bval = ci.bval
            prev_is_bra = False
        else:
            # branch-related instruction

            # create relations
            branch_target_sval = int(ci.sinstr.full.split()[-1])
            branch_target_bval = sval2bval(branch_target_sval)
            branch_relations.add( (ci.bval,branch_target_bval) )
            if opcode != "bra":
                is_fall_through = True
                fall_through_parent = ci.bval
            else:
                is_fall_through = False
                prev_is_bra = True
            
            prev_bval = ci.bval

    # remove extra edges
    # (1) if a "from" edge is in both `fall_relations` and `branch_relations`, 
    # remove it from `branch_relations`
    branch_relations = [i for i in list(branch_relations) if i not in list(fall_relations)]
    # add relations to `base`
    for _from,to in list(fall_relations):
        base.append(f"bb{_from}:s -> bb{to}:n [label=\"fall-through\"];")
    for _from,to in list(branch_relations):
        base.append(f"bb{_from}:s -> bb{to}:n [label=\"branch\"];")

    base.append('}')
    return "\n".join(base)

