from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Tuple, Dict, Optional, Iterable
import csv, os, time, argparse, sys

# Initialize coordinate with its row and column 
Coord = Tuple[int, int]

def peers_of(r, c):
    #Get peer coordinates for cell (r, c)
    row = set()
    j = 0
    while j < 9:
        if j != c:
            row.add((r, j))
        j += 1

    col = set()
    i = 0
    while i < 9:
        if i != r:
            col.add((i, c))
        i += 1

    br, bc = (r // 3) * 3, (c // 3) * 3

    box = set()
    i = br
    while i < br + 3:
        j = bc
        while j < bc + 3:
            if not (i == r and j == c):
                box.add((i, j))
            j += 1
        i += 1
        
    return row | col | box

# Precompute coordinate list and each cell's peers once (saves time in the solver)
ALL_COORDS: List[Coord] = []
r = 0
while r < 9:
    c = 0
    while c < 9:
        ALL_COORDS.append((r, c))
        c += 1
    r += 1

PEERS: Dict[Coord, Set[Coord]] = {}
for coord in ALL_COORDS:
    r_val = coord[0]
    c_val = coord[1]
    the_peers = peers_of(r_val, c_val)
    PEERS[coord] = the_peers

# -----------------------------
# SECTION: INPUT (read files)
# -----------------------------

 # Read a Sudoku grid from .csv or .txt and return a 9x9 list of ints
    # - Allowed empty markers: 0, '.', or blank
    # - .csv branch uses Python's csv.reader (yields list[str] per row)
    # - .txt branch accepts either '530070000' style lines OR space-separated tokens

def read_sudoku(path):

    _, ext = os.path.splitext(path) # get file extension
    ext = ext.lower() 

    grid = []

    if ext == ".csv":
        with open(path, newline="") as f:
            rd = csv.reader(f) # lists of strings

            for raw_row in rd:
                if not raw_row: # if empty row, skip
                    continue
                vals = []
                index = 0
                # Only consider first 9 columns in the row
                while index < 9 and index < len(raw_row):
                    cell = raw_row[index]
                    # Make sure it's a string and strip surrounding whitespace
                    token = ("" if cell is None else str(cell)).strip()
                    if token == "" or token == "." or token == "0":
                        v = 0
                    else:
                        try:
                            v = int(token)
                        except ValueError: # If it isn't a valid integer (e.g., "x"), treat as empty (0)
                            v = 0
                        if v < 0 or v > 9: # Extra safety: keep only values in 0..9
                            v = 0
                    
                    vals.append(v)
                    index += 1

                if len(vals) == 9:
                    grid.append(vals)

    else:
        # TEXT FILE READER:
        # Accept two common formats:
        # 1) compact digits like "530070000" (dots allowed, spaces ignored)
        # 2) space-separated tokens "5 3 0 0 7 0 0 0 0"
        with open(path) as f:
            for line in f:
                if line is None:
                    continue
                line = line.strip() 
                if line == "":
                    continue

                row = []
                
                # compact style
                cleaned = ""
                k = 0
                while k < len(line):
                    ch = line[k]
                    if ch.isdigit() or ch == ".":
                        cleaned += ch
                    k += 1

                if len(cleaned) >= 9:
                    idx = 0
                    while idx < 9:
                        ch = cleaned[idx]
                        if ch == "." or ch == "0":
                            row.append(0)
                        else:
                            try:
                                val = int(ch)
                            except ValueError:
                                val = 0
                            if val < 0 or val > 9:
                                val = 0
                            row.append(val)
                        idx += 1
                
                # space-separated fallback
                if len(row) != 9:
                    replaced = line.replace(".", "0")
                    pieces = replaced.split()
                    tokens = []
                    for t in pieces:
                        if t:
                            tokens.append(t)
                    if len(tokens) >= 9:
                        row = []
                        t_index = 0
                        while t_index < 9:
                            t = tokens[t_index]
                            try:
                                v = int(t)
                            except ValueError:
                                v = 0
                            if v < 0 or v > 9:
                                v = 0
                            row.append(v)
                            t_index += 1

                if len(row) == 9:
                    grid.append(row)

    if len(grid) != 9:
        raise ValueError("Input is not a valid 9x9 Sudoku grid (wrong number of rows).")
    for r in range(9):
        if len(grid[r]) != 9:
            raise ValueError("Input is not a valid 9x9 Sudoku grid (wrong row length).")
    return grid


def is_valid_answer(board):
    
    # Return False if any row/col/box has a duplicate non-zero number
    # Otherwise True. This rejects illegal inputs early

    # rows
    for r in range(9):
        seen = set()
        for c in range(9):
            v = board[r][c]
            if v != 0:
                if v in seen:
                    return False
                seen.add(v)

    # columns
    for c in range(9):
        seen = set()
        for r in range(9):
            v = board[r][c]
            if v != 0:
                if v in seen:
                    return False
                seen.add(v)

    # 3x3 boxes 
    for br in range(0, 9, 3):       # br = 0, 3, 6
        for bc in range(0, 9, 3):   # bc = 0, 3, 6
            seen = set()
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    v = board[r][c]
                    if v != 0:
                        if v in seen:
                            return False
                        seen.add(v)
    return True


def board_complete(board):
    # True if there are no zeros on the board
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return False
    return True


def possible_candidates(board, PEERS):
    
    # Build a 9x9 grid of candidate possible sets, then do a elimination pass
    
    cand = []
    for r in range(9):
        row_sets = []
        for c in range(9):
            v = board[r][c]
            if v != 0:
                row_sets.append({v})
            else:
                row_sets.append({1,2,3,4,5,6,7,8,9})
        cand.append(row_sets)

    # repeatedly remove fixed values from peers until no change
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if len(cand[r][c]) == 1:
                    v = next(iter(cand[r][c]))
                    for peer in PEERS[(r, c)]:
                        pr = peer[0]
                        pc = peer[1]
                        if v in cand[pr][pc] and len(cand[pr][pc]) > 1:
                            cand[pr][pc].remove(v)
                            changed = True
    return cand

def fill_single(board, cand, PEERS):

    # Fill any cell that has exactly one candidate
    # Return False on contradiction (an empty cell left with no candidates)
    
    progress = True
    while progress:
        progress = False

        for r in range(9):
            for c in range(9):
                # fill single answer
                if board[r][c] == 0 and len(cand[r][c]) == 1:
                    v = next(iter(cand[r][c]))
                    board[r][c] = v

                    # remove v from peers
                    for peer in PEERS[(r, c)]:
                        pr = peer[0]
                        pc = peer[1]
                        if v in cand[pr][pc]:
                            cand[pr][pc].discard(v)
                            # contradiction: empty cell with no candidates
                            if board[pr][pc] == 0 and len(cand[pr][pc]) == 0:
                                return False
                    progress = True

        # Check for contradictions anywhere
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and len(cand[r][c]) == 0:
                    return False

    return True


