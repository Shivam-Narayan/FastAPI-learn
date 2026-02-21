@echo off
REM Cross-platform build dispatcher: Bash script is used if available.

REM If the user has Bash (WSL/Git Bash/other), forward all arguments to build.sh.
where bash >nul 2>&1
if %ERRORLEVEL%==0 (
    bash "%~dp0build.sh" %*
    exit /b %ERRORLEVEL%
)

REM Fallback: minimal instructions for native Windows users.
echo "Bash is not available on this system."
echo "Please install Git Bash, WSL, or another Bash environment and rerun the script."
echo "Alternatively, you can perform the build steps manually:"
echo "    pip install -r requirements.txt"
echo "    docker build -t <image> -f ../backend/Dockerfile ../backend"
echo "    (and any version bumping or pushing you need)"
exit /b 1
