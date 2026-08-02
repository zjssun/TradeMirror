@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "BUILD_ROOT=%REPO_ROOT%\release\build"
set "VENV=%BUILD_ROOT%\engine-venv"
set "PYTHON=python"

%PYTHON% -c "import platform, sys; assert platform.architecture()[0] == '64bit', 'Python x64 is required'; assert sys.version_info >= (3, 12), 'Python 3.12 or later is required'" || exit /b 1

if not exist "%VENV%\Scripts\python.exe" (
  %PYTHON% -m venv "%VENV%" || exit /b 1
)

"%VENV%\Scripts\python.exe" -m pip install --upgrade pip || exit /b 1
"%VENV%\Scripts\python.exe" -m pip install -e "%REPO_ROOT%\engine[dev,package]" || exit /b 1

pushd "%REPO_ROOT%\engine"
"%VENV%\Scripts\python.exe" -m pytest || (popd & exit /b 1)
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath "%BUILD_ROOT%\engine-dist" --workpath "%BUILD_ROOT%\pyinstaller-work" TradeMirrorEngine.spec || (popd & exit /b 1)
popd

if not exist "%BUILD_ROOT%\engine-dist\TradeMirrorEngine.exe" (
  echo Engine executable was not created.
  exit /b 1
)

if not exist "%BUILD_ROOT%\engine" mkdir "%BUILD_ROOT%\engine" || exit /b 1
copy /y "%BUILD_ROOT%\engine-dist\TradeMirrorEngine.exe" "%BUILD_ROOT%\engine\TradeMirrorEngine.exe" >nul || exit /b 1

echo Engine build completed: %BUILD_ROOT%\engine\TradeMirrorEngine.exe
