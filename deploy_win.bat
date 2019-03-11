echo Deploying as version %1%

call .\build_win.bat --clean --onefile

zip -j .\dist\athena_win_%1%.zip .\dist\athena.exe
