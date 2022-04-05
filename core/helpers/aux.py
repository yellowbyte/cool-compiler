from ..includes import config

from ..lexer import *

from .logger import *


def subexpression_search(bval, sinstr):
    is_load = False
    opcode = sinstr.opcode  # get just the opcode
    if opcode == "adda" or opcode == "load":
        is_load = True
    if opcode not in config.COMMON_SEARCH[bval]:
        return 0 

    # list of Sinfo
    sinfo_list = config.COMMON_SEARCH[bval][opcode]
    
    if not sinfo_list: 
        # opcode does not exist in `bb` execution path
        return 0  # reserved sval
    
    for sinfo in sinfo_list:
        if is_load and sinfo.sinstr.opcode in ["kill", "store"]:
            # for load instruction,
            # stop searching once `kill` or `store` is found
            return 0
        if sinstr.full == sinfo.sinstr.full and (sinstr.lvar == sinfo.sinstr.lvar or opcode == "const"):
            # right expression is a safety check that makes sure we are only replacing
            # sval of the correct variables 
            # example problem: instr with const 0 replaced with exact instr but const 0 becomes a 
            # without this check, they became the same instruction if a has the value of const 0
            return sinfo.sval
    # opcode exists but not the exact SSA value

    return 0  # reserved sval


def recursion_tracker(func):
    def decorate():

        logging.debug(f"{'-'*config.RECURSIVE_DEPTH} {func.__name__}")
        config.RECURSIVE_DEPTH += 1
        rv = func()
        config.RECURSIVE_DEPTH -= 1

        return rv

    return decorate


def create_bb(bb_type, parent_bval, bb_val=None):
    """
    bb_type: bb1 for CUR_BB, bb2 for OTHER_BB
    parent_bval: the basic block that it comes from
    bb_val: basic block to add to. None if it is a new basic block 
    """
    # get old vars
    old_vars = config.VARS_ASSIGN[parent_bval]
    old_dominators = config.COMMON_SEARCH[parent_bval]

    # denote working on a new basic block or not
    # if `bb_val` not None, then not working on new basic block
    if not bb_val:
        config.CUR_BB_VAL = config.BB_VALS.pop(0)  # get a new basic block number
    else:
        config.CUR_BB_VAL = bb_val  # use an existing basic block number

    # copy over old vars 
    for var,val in old_vars.items():
        config.VARS_ASSIGN[config.CUR_BB_VAL][var] = val

    # copy over old dominators 
    for opcode,sinfo_list in old_dominators.items():
        config.COMMON_SEARCH[config.CUR_BB_VAL][opcode] = sinfo_list

    if bb_type == "bb1":
        config.TMP_BB1.insert(0, [])
        return config.BBinfo(config.TMP_BB1[0], config.CUR_BB_VAL)
    elif bb_type == "bb2":
        config.TMP_BB2.insert(0, [])
        return config.BBinfo(config.TMP_BB2[0], config.CUR_BB_VAL)
        
    return ()


def delete_bb(bb, bb_type):
    """
    bb: basic block to delete
    bb_type: basic block working set to delete from

    edge_sval: sval of last sinstr in `bb`
    """
    # update `config.DELETED_BBS`
    config.DELETED_BBS.add(bb.bval)

    # update `SVAL2INDEX` for sval to eventual code index mapping
    cur_index = len(config.CODE)
    edge_sval = None
    for num,i in enumerate(bb.storage):
        config.SVAL2INDEX[i.sval] = cur_index
        edge_sval = i.sval
        cur_index += 1    

    # add working basic block to eventual code
    config.CODE.extend(bb.storage)

    # remove finished bb
    if bb_type == "bb1":
        config.TMP_BB1 = config.TMP_BB1[1:]
        # older bb on the stack
        if len(config.TMP_BB1) != 0 and len(config.TMP_BB1[0]) != 0:
            # assign to next BB on the stack
            config.CUR_BB = config.BBinfo(config.TMP_BB1[0], config.TMP_BB1[0][0].bval)
    if bb_type == "bb2":
        config.TMP_BB2 = config.TMP_BB2[1:]
        # older bb on the stack
        if len(config.TMP_BB2) != 0 and len(config.TMP_BB2[0]) != 0:
            # assign to next BB on the stack
            config.OTHER_BB = config.BBinfo(config.TMP_BB2[0], config.TMP_BB2[0][0].bval)

    return edge_sval


def get_deleted_bbs():
    return config.DELETED_BBS


def update_if_phi(bb, branch_bval, lr_bb_val):
    """
    bb: join block
    branch_bval: basic block number of the if block
    lr_bb_val: list of then and else (if exist) block numbers 
    """
    og_vars = config.VARS_ASSIGN[branch_bval]
    og_vars_set = set(og_vars.items())

    # process then block
    left_bb_val = lr_bb_val[0]
    bb_vars = config.VARS_ASSIGN[left_bb_val]
    bb_vars_set = set(bb_vars.items())        
    phis = bb_vars_set - og_vars_set
        
    # create phi's instructions
    for phi in phis: 
        var = phi[0]
        val = phi[1]

        sinstr = config.SInstr(f"phi {val} {og_vars[var]}", "", "")
        bb.storage.append( config.CODEinfo(bb.bval, config.CUR_SSA_VAL, sinstr) )
        # update `VARS_ASSIGN` for downstream
        config.VARS_ASSIGN[bb.bval][var] = config.CUR_SSA_VAL
        config.CUR_SSA_VAL += 1

    # process else block (if exists)
    if len(lr_bb_val) == 1:
        return None
    og_vars = config.VARS_ASSIGN[branch_bval]
    val2var = {v: k for k, v in og_vars.items()}  # reverse of left bb's vars_assign dict

    # process else block
    right_bb_val = lr_bb_val[1]
    bb_vars = config.VARS_ASSIGN[right_bb_val]
    bb_vars_set = set(bb_vars.items())        
    phis = bb_vars_set - og_vars_set

    # create or update existing phi's instructions
    for phi in phis: 
        var = phi[0]
        val = phi[1]
        
        # check if the phi to update already exists in the join block
        # update the second operand of the corresponding phi
        for i,cur_sinstr in enumerate(bb.storage):
            # var exists in join bb's VARS_ASSIGN table AND the corresponding val is the current phi's ssa val
            if var in config.VARS_ASSIGN[bb.bval].keys() and config.VARS_ASSIGN[bb.bval][var] == bb.storage[i].sval:
                # phi is not new
                # update in-place on existing phi
                sinstr_parts = bb.storage[i].sinstr.full.split()[:-1]
                lsval = bb.storage[i].sinstr.lsval
                rsval = bb.storage[i].sinstr.rsval
                sinstr_parts.append(str(val))
                sinstr = " ".join(sinstr_parts)
                bval = bb.storage[i].bval
                sval = bb.storage[i].sval
                bb.storage[i] = config.CODEinfo(bval, sval, config.SInstr(sinstr, lsval, rsval))
                break
        else:
            # var not exists in left parent bb
            sinstr = config.SInstr(f"phi {og_vars[var]} {val}", "", "")
            bb.storage.append( config.CODEinfo(bb.bval, config.CUR_SSA_VAL, sinstr) )
            # update `VARS_ASSIGN` for downstream
            config.VARS_ASSIGN[bb.bval][var] = config.CUR_SSA_VAL
            config.CUR_SSA_VAL += 1

    return None


