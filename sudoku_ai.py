from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Tuple, Dict, Optional, Iterable
import csv, os, time, argparse, sys

# A board coordinate; row and column are 0..8
Coord = Tuple[int, int]

def peers_of(r: int, c: int) -> Set[Coord]:
    #Get peer coordinates for cell (r, c)
    row = {(r, j) for j in range(9) if j != c}
    col = {(i, c) for i in range(9) if i != r}
    br, bc = (r // 3) * 3, (c // 3) * 3
    box = {(i, j) for i in range(br, br + 3) for j in range(bc, bc + 3) if (i, j) != (r, c)}
    return row | col | box

# Precompute coordinate list and each cell's peers once (saves time in the solver)
ALL_COORDS: List[Coord] = [(r, c) for r in range(9) for c in range(9)]
PEERS: Dict[Coord, Set[Coord]] = {coord: peers_of(*coord) for coord in ALL_COORDS}

# -----------------------------
# SECTION: INPUT (read files)
# -----------------------------
def read_sudoku(path: str) -> List[List[int]]:
    
    # Read a Sudoku grid from .csv or .txt and return a 9x9 list of ints.
    # - Allowed empty markers: 0, '.', or blank.
    # - .csv branch uses Python's csv.reader (yields list[str] per row).
    # - .txt branch accepts either '530070000' style lines OR space-separated tokens.
    
    ext = os.path.splitext(path)[1].lower()
    grid: List[List[int]] = []

    if ext == ".csv":
        # CSV READER NOTE:
        # csv.reader returns lists of strings (list[str]). We parse each string cell,
        # strip whitespace, and convert it to an int (0..9). Non-digits become 0.
        with open(path, newline="") as f:
            rd: Iterable[list[str]] = csv.reader(f)  # lists of strings
            for raw_row in rd:
                if not raw_row:             # skip empty CSV rows
                    continue
                vals: List[int] = []
                # Only consider first 9 columns in the row
                for cell in raw_row[:9]:
                    # 'cell' might be '', ' 8 ', '0', '.', 'x', etc. Keep it robust.
                    token = (cell or "").strip()
                    if token in ("", "0", "."):
                        # Empty markers map to 0 (our "empty" representation)
                        vals.append(0)
                    else:
                        try:
                            # int('8') -> 8; int('x') would raise ValueError
                            v = int(token)
                        except ValueError:
                            # If not a valid integer, treat as empty (0).
                            v = 0
                        # Enforce bounds 0..9 (any weird numbers become 0)
                        if v < 0 or v > 9:
                            v = 0
                        vals.append(v)
                # Only accept rows that decode to exactly 9 numbers
                if len(vals) == 9:
                    grid.append(vals)

    else:
        # TEXT FILE READER:
        # Accept two common formats:
        # 1) compact digits like "530070000" (dots allowed, spaces ignored)
        # 2) space-separated tokens "5 3 0 0 7 0 0 0 0"
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:                 # skip blank lines
                    continue

                row: List[int] = []

                # First try: compact style (9+ digits/dots in line). We squeeze out spaces.
                if len(line) >= 9 and all(ch.isdigit() or ch == "." for ch in line.replace(" ", "")):
                    compact = "".join(ch for ch in line if (ch.isdigit() or ch == "."))
                    if len(compact) >= 9:
                        for ch in compact[:9]:
                            row.append(0 if ch in ("0", ".") else int(ch))

                # Fallback: space-separated style (turn '.' into '0' and split)
                if len(row) != 9:
                    tokens = [t for t in line.replace(".", "0").split() if t]
                    if len(tokens) >= 9:
                        row = []
                        for t in tokens[:9]:
                            try:
                                v = int(t)
                            except ValueError:
                                v = 0
                            if v < 0 or v > 9:
                                v = 0
                            row.append(v)

                if len(row) == 9:
                    grid.append(row)

    # Final shape check: must be exactly 9 rows of 9 ints each
    if len(grid) != 9 or any(len(r) != 9 for r in grid):
        raise ValueError("Input is not a valid 9x9 Sudoku grid.")
    return grid

