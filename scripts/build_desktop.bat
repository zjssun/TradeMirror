@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "BUILD_ROOT=%REPO_ROOT%\release\build"

where npm >nul 2>nul || (echo npm is required. & exit /b 1)
where cargo >nul 2>nul || (echo Cargo is required. & exit /b 1)

call npm ci --prefix "%REPO_ROOT%\frontend" || exit /b 1
call npm run build --prefix "%REPO_ROOT%\frontend" || exit /b 1

pushd "%REPO_ROOT%\desktop\tauri"
cargo tauri build --no-bundle -- --locked || (popd & exit /b 1)
popd

if not exist "%REPO_ROOT%\desktop\tauri\target\release\trademirror-desktop.exe" (
  echo Desktop executable was not created.
  exit /b 1
)

if not exist "%BUILD_ROOT%\desktop" mkdir "%BUILD_ROOT%\desktop" || exit /b 1
copy /y "%REPO_ROOT%\desktop\tauri\target\release\trademirror-desktop.exe" "%BUILD_ROOT%\desktop\TradeMirror.exe" >nul || exit /b 1

echo Desktop build completed: %BUILD_ROOT%\desktop\TradeMirror.exe
