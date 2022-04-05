from collections import defaultdict,namedtuple


TOKENIZER = None
##### ~~~~~~~~~~ EACH BASIC BLOCK HAS AN ENTRY #####

# Each function is a list of three-tuple.
# For each three-tuple...
# First element is a number that is unique for each basic block. It indexes into the VarAssign and SearchCommon table
# Second element is SSA value. 
# Third element is the SSA instruction. 
CODEinfo = namedtuple("CODEinfo", ["bval", "sval", "sinstr"])

# to represent an sinstr
class SInstr: 
    def __init__(self, sinstr, *_vars):
        self._full = sinstr
        items = self._full.split()
        if items:
            self.opcode = items[0]  # opcode will never change 
        else: 
            self.opcode = ""
        self._lsval = None
        self._rsval = None
        self.sval_extra = []
        self.lvar = None
        self.rvar = None

        if len(items) > 3:
            # call sinstr can have more operands
            # otherwise, the SSA has at most 2 operands
            self.lsval = items[1]
            self.rsval = items[2]
            self.lvar = _vars[0]
            self.rvar = _vars[1]
            self.sval_extra = items[3:]
        elif len(items) == 3: 
            self.lsval = items[1]
            self.rsval = items[2]
            self.lvar = _vars[0]
            self.rvar = _vars[1]
        elif len(items) == 2:  # only one argument
            self.lsval = items[1]
            self.lvar = _vars[0]


    @property
    def full(self):
        if self.sval_extra:
            instr = " ".join([self.opcode, self.lsval, self.rsval])
            args = " ".join(self.sval_extra)
            return " ".join([instr, args])
        elif self.rsval:
            return " ".join([self.opcode, self.lsval, self.rsval])
        elif self.lsval:
            return " ".join([self.opcode, self.lsval])
        else:
            return self.opcode

    @property
    def lsval(self):
        return self._lsval

    @property
    def rsval(self):
        return self._rsval

    @lsval.setter
    def lsval(self, sval):
        self._lsval = sval

    @rsval.setter
    def rsval(self, rval):
        self._rsval = rval


# deleted basic blocks (track their bval)
DELETED_BBS = set()

# Every instruction computes a value. The table (dictionary) states 
# which value is currently representing which variable of the original program. 
VARS_ASSIGN = defaultdict(dict)

# basic block info
# storage: list to store svals/sinstrs for basic block
# bval: number that denotes basic block's `CUR_BB_VAL` at time of creation
BBinfo = namedtuple("BBinfo", ["storage", "bval"])

# Search data structures for common subexpression elimination
# This table gives the linked list (list but we push to head) for each opcode (per basic block)
# For the linked list, it is a list of Sinfo
Sinfo = namedtuple("Sinfo", ["sval", "sinstr"])
COMMON_SEARCH = defaultdict(lambda: defaultdict(list))
##### ~~~~~~~~~~ EACH BASIC BLOCK HAS AN ENTRY #####

# Key: SSA value. Value: index in list
# Needs this to walk the IR (visualization)
# Needs this to identify parent basic blocks after getting SSA values from `ORIGINS`
SVAL2INDEX = dict()

# Given a basic block, identify parent basic blocks
# Key: SSA value. Value: list of SSA values
ORIGINS = defaultdict(list)

# List that contains the eventual code
CODE = list()

# Temporary basic blocks for construction
# Need at most 4 working BB for construction at the same time
# EX: constructing an if-statement will require 5
# list of list to handle nested if/while 
TMP_BB1 = []
TMP_BB2 = []
CUR_BB = None  # current working basic block
               # will point to one of the lists in TMP_BB*
PREV_BB = None  # keep track of previous `CUR_BB`
                # useful for implementing while-statement

# First basic block (dominates all other)
# To store constants
# doesn't actually exist in the eventual control flow graph
BB0 = list()

# First element of the three-tuple
CUR_BB_VAL = 0  # BB0 has a `CUR_BB_VAL` of 0
                  # Currently available basic block number not used
BB_VALS = list(range(1,1000))

# Second element of the three-tuple
CUR_SSA_VAL = 1  # currently available SSA value not used
                 # 0 reserved for NOT FOUND rv by `subexpression_search` 

# global offsets for array
CUR_OFFSETS = 0
GLOBAL_OFFSETS = 0
CUR_LIST = list()  # list of initial size for array
                   # EX: 
                   #    array[1][2][1] -> [1,2,1]

# keep track of array dimensions
ARRAY_DIMS = dict()

# constant 0 var
CONST0_VAR = None 
# constant 4 var
CONST4_VAR = None 

# differentiate between loading or storing. For array
IS_ARRAY_INSTR = False
ID_IS_ARRAY = False

INSIDE_LOOP = False
ADD_KILL = False

FILE = None

# Current lookahead token for parser
TOKEN = None 

# Keep track of functions (name to sval mapping)
FUNCTIONS = dict()

# Previously assigned edge sval (i.e., basic block before branching)
PREV_EDGE_SVAL = []

# Recursive depths. For debugging 
RECURSIVE_DEPTH = 1

# If parser is at function declaration, not function body
IN_FUNC_DECL = False
