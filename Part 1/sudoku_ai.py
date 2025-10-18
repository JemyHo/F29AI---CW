from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Tuple, Dict, Optional, Iterable
import csv, os, time, argparse, sys
from copy import deepcopy
import time as _time
import tkinter as tk
from tkinter import filedialog, messagebox

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

# -----------------------------
# SECTION: Solving 
# -----------------------------
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


def select_mrv_cell(board, cand):

    # Return the (r, c) of an empty cell with the Minimum Remaining Values/fewest candidates

    best = None
    best_size = 10
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                k = len(cand[r][c])
                if k < best_size:
                    best_size = k
                    best = (r, c)
    return best

def solve_backtrack(board, cand, PEERS, depth=0):
    # 1) do all singles first
    if not fill_single(board, cand, PEERS):
        return False

    # 2) solved?
    if board_complete(board):
        return True

    # 3) pick the least candidate empty cell
    cell = select_mrv_cell(board, cand)
    if cell is None:  # defensive; board_complete should catch this
        return True
    r, c = cell
    # dead-end if no candidates
    if len(cand[r][c]) == 0:
        return False

    # 4) try candidates (smallest first like the video)
    for v in sorted(cand[r][c]):
        b2 = deepcopy(board)
        c2 = deepcopy(cand)

        # assign the guess
        b2[r][c] = v
        c2[r][c] = {v}

        # forward-check: remove v from peers immediately
        consistent = True
        for pr, pc in PEERS[(r, c)]:
            if v in c2[pr][pc]:
                c2[pr][pc].discard(v)
                if b2[pr][pc] == 0 and len(c2[pr][pc]) == 0:
                    consistent = False
                    break

        # recurse if still consistent
        if consistent:
            solved = solve_backtrack(b2, c2, PEERS, depth + 1)
            if solved: 
            # copy solution back
                for rr in range(9):
                    for cc in range(9):
                        board[rr][cc] = b2[rr][cc]
            return True

    # 5) no candidate worked here → backtrack
    return False

def solve_sudoku(board, PEERS):
    
    # Return (ok, solved_board, ms). 'board' is modified in place.
    
    start = time.perf_counter()

    if not is_valid_answer(board):
        ms = (time.perf_counter() - start) * 1000.0
        return False, board, ms

    cand = possible_candidates(board, PEERS)
    solve = solve_backtrack(board, cand, PEERS)

    ms = (time.perf_counter() - start) * 1000.0
    return solve, board, ms

# -----------------------------
# SECTION: GUI 
# -----------------------------
CELL_SIZE = 44
GRID_SIZE = CELL_SIZE * 9
PAD = 10
FONT_CELL = ("Helvetica", 16, "bold")

class SudokuViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Viewer")

        # board model (9x9 ints, 0 = empty)
        self.board = [[0]*9 for _ in range(9)]

        # canvas for grid + numbers
        self.canvas = tk.Canvas(
            self.root,
            width=GRID_SIZE + 2*PAD,
            height=GRID_SIZE + 2*PAD,
            bg="white"
        )
        self.canvas.grid(row=0, column=0, columnspan=2, padx=8, pady=8)

        # buttons
        tk.Button(self.root, text="Load…", command=self.on_load).grid(
            row=1, column=0, sticky="ew", padx=6, pady=6
        )
        tk.Button(self.root, text="Clear", command=self.on_clear).grid(
            row=1, column=1, sticky="ew", padx=6, pady=6
        )

        # initial draw (blank grid)
        self.draw_board(self.board)

    def on_clear(self):
        self.board = [[0]*9 for _ in range(9)]
        self.draw_board(self.board)

    def on_load(self):
        path = filedialog.askopenfilename(
            title="Open Sudoku (.csv or .txt)",
            filetypes=[("Sudoku Files", "*.csv *.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            grid = read_sudoku(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            return
        self.board = deepcopy(grid)
        self.draw_board(self.board)

    def draw_board(self, board):
        self.canvas.delete("all")
        x0 = PAD
        y0 = PAD

        # cells + digits
        for r in range(9):
            for c in range(9):
                x1 = x0 + c * CELL_SIZE
                y1 = y0 + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                # cell rect
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="#bbb")

                # number (if any)
                v = board[r][c]
                if v != 0:
                    self.canvas.create_text(
                        (x1+x2)//2, (y1+y2)//2,
                        text=str(v),
                        font=FONT_CELL
                    )

        # heavy 3x3 box lines
        for i in range(10):
            width = 3 if i % 3 == 0 else 1
            xi = x0 + i * CELL_SIZE
            yi = y0 + i * CELL_SIZE
            # vertical
            self.canvas.create_line(xi, y0, xi, y0 + GRID_SIZE, fill="#333", width=width)
            # horizontal
            self.canvas.create_line(x0, yi, x0 + GRID_SIZE, yi, fill="#333", width=width)


def launch_viewer(initial_path=None):
    root = tk.Tk()
    app = SudokuViewer(root)

    # if a path was provided on launch, try to load it
    if initial_path:
        try:
            grid = read_sudoku(initial_path)
            app.board = deepcopy(grid)
            app.draw_board(app.board)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")

    root.mainloop()

# If run directly:
# - with a path: shows that puzzle
# - without a path: shows blank grid
if __name__ == "__main__":
    # If user passed a file path (txt/csv), load it; else show blank
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    launch_viewer(path_arg)