# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""


class UnknownReFSVersionError(Exception):
    pass


class CheckpointKeyError(Exception):

    def __init__(self, reserved):
        self.reserved = reserved

    def __str__(self):
        return f"<Reserved page: {self.reserved}>"


class InvalidMetaPageSignatureError(Exception):
    pass


class LCNTupleTypeError(Exception):
    pass


class CPCValueNotFoundError(Exception):
    pass


class CPCValueDoNotMatchError(Exception):
    pass