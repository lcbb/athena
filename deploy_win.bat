python build_preflight.py

for /f %%i in ('python athena_version.py') do set VERSION=%%i

echo Deploying as version %VERSION%

call .\build_win.bat --clean --noconfirm --onefile

del /s /f /q ".\Athena"
mkdir Athena
xcopy "dist\Athena.exe" "Athena\"
xcopy "README.txt" "Athena\"
xcopy "LICENSE" "Athena\"

set ZIPFILE=dist/athena_win_%VERSION%.zip
echo Creating %ZIPFILE%
zip -r -j %ZIPFILE% Athena
