import sys

from core import *


# USAGE: python main.py <filepath to smpl source file> [<function name>]
if __name__ == "__main__":
    filepath = sys.argv[1]
    if len(sys.argv) == 2:
        # if no function specified, generated DOT code will be for main
        func = "main"
    else: 
        func = sys.argv[2]
    with open(filepath) as f:
        Parser(f)

    code = config.CODE
    digraph = vis(code,func)
    print(digraph)
