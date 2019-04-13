Athena: A Toolkit for DNA Construction

### Restrictions on input files ###

PERDIX and METIS expect all inputs to be in the XY plane.

All tools will reject PLY input files that define a vertex
that is not used in at least one polygon.

### Setting up a development environment ###

How to run the project from a working directory:

> virtualenv env
> source env/activate
> pip install -r requirements.txt
> python src/athena.py
> ./build_win.bat <any additional arg for pyinstaller, e.g. --onefile>
