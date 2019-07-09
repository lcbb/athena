Athena: A Toolkit for DNA Construction

### Restrictions on input files ###

Only PLY files are accepted.

PERDIX and METIS, the 2D sequence tools, require all
input geometry to be in the XY plane with Z=0 for all vertices.
All other input files will be treated as 3D.

All sequence tools will reject PLY input files which define a vertex
that is not used in at least one polygon.  Athena can display such
files, but they cannot be processed to generate output files.

### Setting up a development environment ###

How to run the project from a working directory:

> virtualenv env
> source env/activate
> pip install -r requirements.txt
> python src/athena.py
> ./build_win.bat <any additional arg for pyinstaller, e.g. --onefile>
