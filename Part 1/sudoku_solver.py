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
    #Get peer coordinates of a coordinate (r, c)
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

# Pre define Stats to record 
class Stats:
    def __init__(self):
        self.steps = 0
        self.recursive_calls = 0
        self.backtracks = 0
        self.start = 0.0
        self.end = 0.0

# -----------------------------
# SECTION: INPUT (read files)
# -----------------------------

 # Read a Sudoku grid from .csv or .txt and return a 9x9 list of ints
    # - Allowed empty markers: 0, '.', or blank
    # - .csv branch uses Python's csv.reader (yields list[str] per row)
    # - .txt branch accepts either '530070000' style lines OR space-separated tokens

def validate_sudoku_value(token):
    #Convert a token to an int in 0..9; treat non-numeric or out-of-range as 0.
    if token is None:
        return 0
    s = str(token).strip()
    if s == "" or s == "." or s == "0":
        return 0
    try:
        v = int(s)
    except ValueError:
        return 0
    return v if 0 <= v <= 9 else 0


def process_compact_line(line):
    #Process compact digit lines (like '530070000'). Returns a 9-element list or [].
    if line is None:
        return []
    cleaned = ''.join(ch for ch in line if ch.isdigit() or ch == '.')
    if len(cleaned) < 9:
        return []
    row = []
    for ch in cleaned[:9]:
        row.append(validate_sudoku_value(ch))
    return row


def process_space_separated_line(line):
    #Process space-separated token lines. Returns a 9-element list or [].
    if line is None:
        return []
    replaced = line.replace('.', '0')
    pieces = [t for t in replaced.split() if t]
    if len(pieces) < 9:
        return []
    row = [validate_sudoku_value(pieces[i]) for i in range(9)]
    return row


def read_sudoku(path):

    _, ext = os.path.splitext(path) # get file extension
    ext = ext.lower() 
    grid = []

    if ext == ".csv":
        with open(path, newline="") as f:
            rd = csv.reader(f)
            for raw_row in rd:
                if not raw_row:
                    continue
                # only first 9 tokens per row
                vals = [validate_sudoku_value(raw_row[i]) for i in range(min(9, len(raw_row)))]
                if len(vals) == 9:
                    grid.append(vals)
    else:
        with open(path) as f:
            for line in f:
                if line is None:
                    continue
                line = line.strip()
                if line == "":
                    continue

                # try compact first, then space-separated
                row = process_compact_line(line)
                if len(row) != 9:
                    row = process_space_separated_line(line)
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

def has_duplicates_nonzero(seq):
    #Return True if seq contains duplicate non-zero values.
    seen: Set[int] = set()
    for v in seq:
        if v != 0:
            if v in seen:
                return True
            seen.add(v)
    return False


def rows_valid(board):
    for r in range(9):
        if has_duplicates_nonzero(board[r]):
            return False
    return True


def cols_valid(board):
    for c in range(9):
        col = [board[r][c] for r in range(9)]
        if has_duplicates_nonzero(col):
            return False
    return True


def boxes_valid(board):
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            vals = []
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    vals.append(board[r][c])
            if has_duplicates_nonzero(vals):
                return False
    return True


def is_valid_board(board):
    return rows_valid(board) and cols_valid(board) and boxes_valid(board)


def board_complete(board):
    # True if there are no zeros on the board
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return False
    return True

def initial_candidate_grid(board):
    #Create the initial candidate grid from `board`.
    #Filled cells get singleton sets; empty cells get {1..9}.
    
    full = {1,2,3,4,5,6,7,8,9}
    cand = []
    for r in range(9):
        row_sets: List[Set[int]] = []
        for c in range(9):
            v = board[r][c]
            if v != 0:
                row_sets.append({v})
            else:
                row_sets.append(set(full))
        cand.append(row_sets)
    return cand


def peers_elimination(cand, peers):
    #Iteratively remove singleton values from peers until no change.
    
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if len(cand[r][c]) == 1:
                    v = next(iter(cand[r][c]))
                    for pr, pc in peers[(r, c)]:
                        if v in cand[pr][pc]:
                            cand[pr][pc].discard(v)
                            changed = True
    return cand

def possible_candidates(board, PEERS):
    #Returns possible candidates for each empty cell "0".
    cand = initial_candidate_grid(board)
    cand = peers_elimination(cand, PEERS)
    return cand

def update_candidates(board, cand, coord, value, peers):
    #Remove `value` from candidate sets of coord's peers.
    #Returns False when a contradiction is produced (an empty candidate set for an empty cell).
    r, c = coord
    for pr, pc in peers[(r, c)]:
        if value in cand[pr][pc]:
            cand[pr][pc].discard(value)
            if board[pr][pc] == 0 and len(cand[pr][pc]) == 0:
                return False
    return True

def fill_single(board, cand, PEERS, stats: Stats | None = None):
    
    # Fill any cell with exactly one candidate.
    # If stats is provided, count each placement as a step.
    # Return False on contradiction; True otherwise.
    progress = True
    while progress:
        progress = False

        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and len(cand[r][c]) == 1:
                    v = next(iter(cand[r][c]))
                    board[r][c] = v
                    if stats is not None:
                        stats.steps += 1  # count deterministic placement

                    # remove v from peers (use helper)
                    if not update_candidates(board, cand, (r, c), v, PEERS):
                        return False
                    progress = True

        # global candidate contradiction check
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

def solve_backtrack(board, cand, PEERS, stats: Stats | None = None, depth=0):
    if stats is not None:
        stats.recursive_calls += 1

    # 1) singles
    if not fill_single(board, cand, PEERS, stats=stats):
        return False

    # 2) done?
    if board_complete(board):
        return True

    # 3) MRV cell
    cell = select_mrv_cell(board, cand)
    if cell is None:
        return True
    r, c = cell
    if len(cand[r][c]) == 0:
        return False

    # 4) try candidates
    for v in sorted(cand[r][c]):
        b2 = deepcopy(board)
        c2 = deepcopy(cand)

        b2[r][c] = v
        c2[r][c] = {v}
        if stats is not None:
            stats.steps += 1  # count the guess

        # forward-check using helper on the trial copy
        consistent = update_candidates(b2, c2, (r, c), v, PEERS)

        if consistent and solve_backtrack(b2, c2, PEERS, stats=stats, depth=depth+1):
            # copy solution up
            for rr in range(9):
                for cc in range(9):
                    board[rr][cc] = b2[rr][cc]
            return True

        if stats is not None:
            stats.backtracks += 1  # this guess failed

    return False

def solve_sudoku(board, PEERS): #Wrapper that organize and return things you need.
    stats = Stats()
    stats.start = _time.perf_counter() 

    if not is_valid_board(board):
        stats.end = _time.perf_counter()
        ms = (stats.end - stats.start) * 1000.0
        return False, board, ms, stats

    cand = possible_candidates(board, PEERS)
    ok = solve_backtrack(board, cand, PEERS, stats=stats)

    stats.end = _time.perf_counter()
    ms = (stats.end - stats.start) * 1000.0
    return ok, board, ms, stats

# -----------------------------
# SECTION: GUI 
# -----------------------------
CELL_SIZE = 44
GRID_SIZE = CELL_SIZE * 9
PAD = 10
FONT_CELL = ("Helvetica", 16, "bold")

class SudokuViewer:
    def __init__(self, root):
        # keep a handle to the Tk root window
        self.root = root
        self.root.title("Sudoku Viewer")

        # a 9x9 board (ints, 0 means empty)
        self.board = [[0] * 9 for _ in range(9)]

        #  LEFT: drawing canvas
        canvas_width  = GRID_SIZE + 2 * PAD
        canvas_height = GRID_SIZE + 2 * PAD

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="white"
        )
        # put the canvas at (row=0, col=0); it spans 3 rows vertically
        self.canvas.grid(row=0, column=0, rowspan=3, padx=8, pady=8)

        # ---------- RIGHT: controls + stats in a frame ----------
        right = tk.Frame(self.root)
        right.grid(row=0, column=1, sticky="n", padx=(0, 10), pady=8)

        # --- buttons row-by-row ---
        self.btn_load = tk.Button(right, text="Load…", width=16, command=self.on_load)
        self.btn_load.grid(row=0, column=0, pady=4, sticky="ew")

        self.btn_clear = tk.Button(right, text="Clear", width=16, command=self.on_clear)
        self.btn_clear.grid(row=1, column=0, pady=4, sticky="ew")

        self.btn_solve = tk.Button(right, text="Solve", width=16, command=self.on_solve)
        self.btn_solve.grid(row=2, column=0, pady=4, sticky="ew")

        # spacer (empty label just to add vertical space)
        spacer = tk.Label(right, text="")
        spacer.grid(row=3, column=0, pady=(6, 0))

        # --- stats labels use StringVars so we can update text later ---
        self.var_time  = tk.StringVar(value="Time: —")
        self.var_steps = tk.StringVar(value="Steps: 0")
        self.var_calls = tk.StringVar(value="Recursive calls: 0")
        self.var_backs = tk.StringVar(value="Backtracks: 0")

        self.lbl_time  = tk.Label(right, textvariable=self.var_time,  anchor="w", width=24)
        self.lbl_steps = tk.Label(right, textvariable=self.var_steps, anchor="w", width=24)
        self.lbl_calls = tk.Label(right, textvariable=self.var_calls, anchor="w", width=24)
        self.lbl_backs = tk.Label(right, textvariable=self.var_backs, anchor="w", width=24)

        self.lbl_time.grid(row=4, column=0, sticky="w", pady=2)
        self.lbl_steps.grid(row=5, column=0, sticky="w", pady=2)
        self.lbl_calls.grid(row=6, column=0, sticky="w", pady=2)
        self.lbl_backs.grid(row=7, column=0, sticky="w", pady=2)

        # draw a blank grid to start
        self.draw_board(self.board)

    def _reset_stats_labels(self):
        """Reset the right-hand stats text to defaults."""
        self.var_time.set("Time: —")
        self.var_steps.set("Steps: 0")
        self.var_calls.set("Recursive calls: 0")
        self.var_backs.set("Backtracks: 0")

    def on_clear(self):
        """Clear the current board and stats, then redraw."""
        self.board = [[0] * 9 for _ in range(9)]
        self._reset_stats_labels()
        self.draw_board(self.board)

    def on_load(self):
        #Open a file chooser, read a Sudoku puzzle, and display it.
        filetypes = [("Sudoku Files", "*.csv *.txt"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(title="Open Sudoku (.csv or .txt)",
                                          filetypes=filetypes)
        if not path:
            return  # user canceled the dialog

        try:
            grid = read_sudoku(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            return

        self.board = deepcopy(grid)
        self._reset_stats_labels()
        self.draw_board(self.board)

    def on_solve(self):
        #Run the solver on a copy, update stats, and show the solved grid.
        # ensure the board isn't all zeros
        has_any_value = any(any(cell != 0 for cell in row) for row in self.board)
        if not has_any_value:
            messagebox.showinfo("Info", "Load a puzzle first.")
            return

        # solver mutates in place → work on a copy
        bcopy = deepcopy(self.board)

        # solve_sudoku returns (ok, solved_board, elapsed_ms, stats)
        ok, solved_board, elapsed_ms, stats = solve_sudoku(bcopy, PEERS)

        # update right-hand stats panel
        self.var_time.set(f"Time: {elapsed_ms:.2f} ms")
        self.var_steps.set(f"Steps: {stats.steps}")
        self.var_calls.set(f"Recursive calls: {stats.recursive_calls}")
        self.var_backs.set(f"Backtracks: {stats.backtracks}")

        if not ok:
            messagebox.showwarning("Unsolvable", "No solution exists for this puzzle.")
            return

        # copy solved board into the GUI state and redraw
        self.board = solved_board
        self.draw_board(self.board)

    def draw_board(self, board):
        #Paint the 9x9 grid and any digits onto the canvas.
        self.canvas.delete("all")

        x0 = PAD
        y0 = PAD

        # draw 81 cells (rectangles) and numbers
        for r in range(9):
            for c in range(9):
                x1 = x0 + c * CELL_SIZE
                y1 = y0 + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                # light gray cell borders, white background
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="white",
                    outline="#bbb"
                )

                value = board[r][c]
                if value != 0:
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=str(value),
                        font=FONT_CELL
                    )

        # heavier lines to outline the 3x3 boxes
        for i in range(10):
            line_width = 3 if i % 3 == 0 else 1

            # vertical line at column i
            xi = x0 + i * CELL_SIZE
            self.canvas.create_line(xi, y0, xi, y0 + GRID_SIZE,
                                    fill="#333", width=line_width)

            # horizontal line at row i
            yi = y0 + i * CELL_SIZE
            self.canvas.create_line(x0, yi, x0 + GRID_SIZE, yi,
                                    fill="#333", width=line_width)


def launch_viewer(initial_path=None):
    #Create the Tk window and run the viewer. Optionally load a file at start.
    root = tk.Tk()
    app = SudokuViewer(root)

    # if the program was launched with a path, load it immediately
    if initial_path:
        try:
            grid = read_sudoku(initial_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
        else:
            app.board = deepcopy(grid)
            app.draw_board(app.board)

    root.mainloop()

# If run directly:
# - with a path: shows that puzzle
# - without a path: shows a blank grid
if __name__ == "__main__": 
    if len(sys.argv) > 1:
        path_arg = sys.argv[1]
    else:
        path_arg = None
    launch_viewer(path_arg)
