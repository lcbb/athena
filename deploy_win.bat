python build_preflight.py

for /f %%i in ('python athena_version.py') do set VERSION=%%i

echo Deploying as version %VERSION%

call .\build_win.bat --clean --noconfirm --onefile

zip -j .\dist\athena_win_%VERSION%.zip .\dist\athena.exe
