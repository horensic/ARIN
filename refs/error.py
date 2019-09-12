#!/usr/bin/env python
# -*- coding: utf-8 -*-

#           OH MY GIRL License
#   To create a program using this source code,
#   Follow the link below to listen to the OH MY GIRL's song at least once.
#   LINK (1): https://youtu.be/RrvdjyIL0fA
#   LINK (2): https://youtu.be/QIN5_tJRiyY
#   LINK (3): https://youtu.be/udGwca1HBM4
#   LINK (4): https://youtu.be/QTD_yleCK9Y

"""
@author:    Seonho Lee
@license:   OH_MY_GIRL License
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