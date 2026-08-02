@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "VERSION=1.0"
set "PACKAGE_ROOT=%REPO_ROOT%\release\TradeMirror"
set "ARCHIVE=%REPO_ROOT%\dist\TradeMirror_Portable_v%VERSION%.zip"
set "CHECKSUM=%ARCHIVE%.sha256"

call "%REPO_ROOT%\scripts\build_engine.bat"
if errorlevel 1 goto :fail

call "%REPO_ROOT%\scripts\build_desktop.bat"
if errorlevel 1 goto :fail

if exist "%PACKAGE_ROOT%" rmdir /s /q "%PACKAGE_ROOT%"
if exist "%ARCHIVE%" del /q "%ARCHIVE%"
if exist "%CHECKSUM%" del /q "%CHECKSUM%"

mkdir "%PACKAGE_ROOT%\engine" || goto :fail
mkdir "%PACKAGE_ROOT%\resources" || goto :fail
mkdir "%PACKAGE_ROOT%\config" || goto :fail
mkdir "%PACKAGE_ROOT%\data" || goto :fail
mkdir "%PACKAGE_ROOT%\logs" || goto :fail

copy /y "%REPO_ROOT%\release\build\desktop\TradeMirror.exe" "%PACKAGE_ROOT%\TradeMirror.exe" >nul || goto :fail
copy /y "%REPO_ROOT%\release\build\engine\TradeMirrorEngine.exe" "%PACKAGE_ROOT%\engine\TradeMirrorEngine.exe" >nul || goto :fail
copy /y "%REPO_ROOT%\packaging\README.txt" "%PACKAGE_ROOT%\README.txt" >nul || goto :fail
copy /y "%REPO_ROOT%\packaging\config.json" "%PACKAGE_ROOT%\config\config.json" >nul || goto :fail
copy /y "%REPO_ROOT%\packaging\placeholders\resources\README.txt" "%PACKAGE_ROOT%\resources\README.txt" >nul || goto :fail
copy /y "%REPO_ROOT%\packaging\placeholders\data\README.txt" "%PACKAGE_ROOT%\data\README.txt" >nul || goto :fail
copy /y "%REPO_ROOT%\packaging\placeholders\logs\README.txt" "%PACKAGE_ROOT%\logs\README.txt" >nul || goto :fail

powershell -NoProfile -ExecutionPolicy Bypass -Command "$stage = Join-Path '%REPO_ROOT%' 'release\\archive-stage'; if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }; New-Item -ItemType Directory -Path $stage | Out-Null; Copy-Item -LiteralPath '%PACKAGE_ROOT%' -Destination (Join-Path $stage 'TradeMirror') -Recurse -Force; Compress-Archive -LiteralPath (Join-Path $stage 'TradeMirror') -DestinationPath '%ARCHIVE%' -CompressionLevel Optimal -Force; Remove-Item -LiteralPath $stage -Recurse -Force" || goto :fail
powershell -NoProfile -ExecutionPolicy Bypass -Command "$hash = (Get-FileHash -LiteralPath '%ARCHIVE%' -Algorithm SHA256).Hash; Set-Content -LiteralPath '%CHECKSUM%' -Value ($hash + '  ' + [IO.Path]::GetFileName('%ARCHIVE%')) -NoNewline" || goto :fail
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $expected = @('TradeMirror/TradeMirror.exe','TradeMirror/engine/TradeMirrorEngine.exe','TradeMirror/config/config.json','TradeMirror/README.txt','TradeMirror/resources/README.txt','TradeMirror/data/README.txt','TradeMirror/logs/README.txt'); $archive = [IO.Compression.ZipFile]::OpenRead('%ARCHIVE%'); try { $actual = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') }); $missing = $expected | Where-Object { $_ -notin $actual }; if ($missing) { throw ('Missing archive entries: ' + ($missing -join ', ')) } } finally { $archive.Dispose() }" || goto :fail

echo.
echo Portable package completed: %ARCHIVE%
echo Checksum: %CHECKSUM%
echo.
pause
exit /b 0

:fail
set "RESULT=%ERRORLEVEL%"
echo.
echo Portable package failed at the preceding command. Exit code: %RESULT%
echo.
pause
exit /b %RESULT%
