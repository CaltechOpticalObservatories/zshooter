@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation
REM
REM Sphinx is invoked through the active Python rather than a bare
REM `sphinx-build` on PATH, so an activated virtualenv is always the one used.

if "%PYTHON%" == "" (
	set PYTHON=python
)
if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=%PYTHON% -m sphinx
)
set SOURCEDIR=source
set BUILDDIR=build

%PYTHON% -c "import sphinx, sphinxcontrib.mermaid, shibuya" >NUL 2>NUL
if errorlevel 1 (
	echo.
	echo.Documentation dependencies are missing from the active environment.
	echo.
	echo.Install them with:
	echo.    pip install -e ".[docs]"
	echo.
	exit /b 1
)

if "%1" == "" goto help

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
