import logging


# log levels
# - CRITICAL
# - ERROR
# - WARNING
# - INFO
# - DEBUG
logging.basicConfig(level=logging.DEBUG)


def cprint(code):
    for ci in code:
        print(f"bval= {ci.bval} sval= {ci.sval} sinstr= {ci.sinstr.full}")
