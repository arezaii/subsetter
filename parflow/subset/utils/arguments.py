import os


"""
Common helpers for checking if command line arguments are valid
"""


def is_valid_file(parser, arg):
    if not os.path.isfile(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg  # return the arg


def is_positive_integer(parser, arg):
    ivalue = int(arg)
    if ivalue < 0:
        raise parser.ArgumentTypeError("%s is an invalid positive int value" % arg)
    else:
        return ivalue


def is_valid_path(parser, arg):
    if not os.path.isdir(arg):
        parser.error("The path %s does not exist!" % arg)
    else:
        return arg  # return the arg


