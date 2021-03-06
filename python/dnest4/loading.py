# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

__all__ = ["my_loadtxt", "loadtxt_rows"]

def my_loadtxt(filename, single_precision=False, delimiter=" "):
    if single_precision:
        return pd.read_csv(filename, header=None, delimiter=delimiter,\
                           comment="#", dtype=np.float32)\
                                    .dropna(axis=1).values
    return pd.read_csv(filename, header=None, delimiter=delimiter, comment="#")\
                                                 .dropna(axis=1).values

def loadtxt_rows(filename, rows, single_precision=False):
    """
    Load only certain rows
    """
    # Open the file
    f = open(filename, "r")

    # Storage
    results = {}

    # Row number
    i = 0

    # Number of columns
    ncol = None

    while(True):
        # Read the line and split by whitespace
        line = f.readline()
        cells = line.split()

        # Quit when you see a different number of columns
        if ncol is not None and len(cells) != ncol:
            break

        # Non-comment lines
        if cells[0] != "#":
            # If it's the first one, get the number of columns
            if ncol is None:
                ncol = len(cells)

            # Otherwise, include in results
            if i in rows:
                if single_precision:
                    results[i] = np.array([float(cell) for cell in cells],\
                                                              dtype="float32")
                else:
                    results[i] = np.array([float(cell) for cell in cells])
            i += 1

    results["ncol"] = ncol
    return results

