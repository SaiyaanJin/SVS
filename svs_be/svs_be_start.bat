@echo off

set PROJECT_PATH=E:\Applications\SVS\svs_be

echo Starting VS Code...

:: Path where VS Code creates workspace data
set WORKSPACE_DIR=%APPDATA%\Code\User\workspaceStorage

:: Snapshot before launching VS Code
dir "%WORKSPACE_DIR%" /b > pre.txt

:: Launch NEW VS Code window (important)
code -n "%PROJECT_PATH%"

echo Waiting for VS Code window to be ready...

:wait_loop
timeout /t 1 >nul

:: Snapshot after launching
dir "%WORKSPACE_DIR%" /b > post.txt

:: Compare snapshots
fc pre.txt post.txt >nul
if errorlevel 1 (
    echo VS Code workspace loaded.
    goto continue_script
)

goto wait_loop

:continue_script

:: Open a fresh terminal inside VS Code
code -r --command "workbench.action.terminal.new"
timeout /t 1 >nul

:: Send your command to the VS Code terminal
code -r --command "workbench.action.terminal.sendSequence" "{\"text\":\"python semvsscada.py\r\"}"

:: Clean temp files
del pre.txt
del post.txt

echo Done.
