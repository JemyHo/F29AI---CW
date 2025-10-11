"""
Simple Sudoku file reader (TXT or CSV).
- Reads a 9x9 grid where empty cells may be: 0, '.' or blank.
- Accepts CSV lines (commas) or whitespace-separated tokens.
- Also accepts a single 9-character token like "530070000" per row.
"""
import sys
import csv
import numpy as np
from typing import Optional

# NOTE: parse_line returns either a numpy 1D array of length 9 or None for blank lines.

def parse_line(line: str) -> Optional[np.ndarray]:
    """
    Parse a single text line into a numpy 1D array of 9 uint8 integers (0 = empty).
    Returns None for blank lines so callers can ignore them.

    Accepted input forms:
      - CSV: "5,3,0,0,7,0,0,0,0"
      - Whitespace: "5 3 0 0 7 0 0 0 0"
      - Compact: "530070000" (single 9-char token)
    Empty cell tokens: '', '0', '.' -> mapped to 0
    """
    line = line.strip()
    if not line:
        # ignore blank lines
        return None

    # Choose splitting strategy: commas -> CSV parser, otherwise whitespace.
    if ',' in line:
        parts = next(csv.reader([line]))  # csv handles quoted values properly
    else:
        parts = line.split()
        # If the row is given as a single 9-character string, split into characters.
        if len(parts) == 1 and len(parts[0]) == 9:
            parts = list(parts[0])

    # build a small Python list for ease, then convert to numpy array
    row_list = []
    for p in parts:
        p = p.strip()
        # Treat empty, '0', or '.' as an empty cell
        if p == '' or p == '0' or p == '.':
            row_list.append(0)
        # Accept digits 1..9
        elif p.isdigit() and 1 <= int(p) <= 9:
            row_list.append(int(p))
        else:
            # Any other token is invalid input for a sudoku cell
            raise ValueError(f"Invalid cell value: {p!r}")

    # Each parsed row must contain exactly 9 cells
    if len(row_list) != 9:
        raise ValueError(f"Row does not have 9 cells: {row_list}")

    return np.array(row_list, dtype=np.uint8)


def load_sudoku(path: str) -> np.ndarray:
    """
    Load a Sudoku puzzle and return a (9,9) numpy.ndarray of dtype uint8.
    Raises ValueError on malformed input.
    """
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            parsed = parse_line(raw)
            if parsed is not None:
                rows.append(parsed)

    if len(rows) != 9:
        raise ValueError(f"File must contain 9 non-empty rows, found {len(rows)}")

    grid = np.stack(rows, axis=0)  # shape (9,9)
    return grid


def print_grid(grid: np.ndarray) -> None:
    """
    Print the grid to stdout. Empty cells (0) are shown as '.' for readability.
    """
    if grid.shape != (9, 9):
        raise ValueError("print_grid expects a (9,9) array")
    for r in range(9):
        print(' '.join(str(int(n)) if n != 0 else '.' for n in grid[r]))


if __name__ == "__main__":
    # Run from the command line: python Sudoku.py puzzle.txt
    if len(sys.argv) < 2:
        print("Usage: python Sudoku.py <puzzle.txt|puzzle.csv>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        grid = load_sudoku(path)
    except Exception as e:
        print("Error loading sudoku:", e)
        sys.exit(1)

    print_grid(grid)