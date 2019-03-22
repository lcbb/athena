import sys
import os, os.path
from pathlib import Path

# Set ATHENA_DIR, the base project path, relative to which files and tools will be found
# and ATHENA_OUTPUT_HOME, the path where an ouput directory will be created
if getattr(sys, 'frozen', False):
    # We're inside a PyInstaller bundle of some kind
    ATHENA_DIR = sys._MEIPASS
    ATHENA_OUTPUT_HOME = Path( sys.executable ).parent.relative_to(Path.cwd())
else:
    # Not bundled, __file__ is within src/athena
    ATHENA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ATHENA_OUTPUT_HOME = '.'

# Set ATHENA_OUTPUT_DIR, the directory where all tools outputs will be written.
# The program will halt here if no such directory can be created
ATHENA_OUTPUT_DIR = Path( ATHENA_OUTPUT_HOME, "athena_outputs")
ATHENA_OUTPUT_DIR.mkdir( parents=False, exist_ok=True )
print("Athena's output directory will be", ATHENA_OUTPUT_DIR)
