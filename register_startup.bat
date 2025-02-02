@echo off
echo Registering CLIP Image Search for startup...

:: Get the current directory
set "SCRIPT_DIR=%~dp0"

:: Create the VBS script to run without console window
echo Set WScript.Shell = CreateObject("WScript.Shell") > "%SCRIPT_DIR%\start_service.vbs"
echo WScript.Shell.CurrentDirectory = "%SCRIPT_DIR%" >> "%SCRIPT_DIR%\start_service.vbs"
echo WScript.Shell.Run """%SCRIPT_DIR%\service.bat""", 0, False >> "%SCRIPT_DIR%\start_service.vbs"

:: Create the startup shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\CLIP_Image_Search.lnk" >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%\start_service.vbs" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "CLIP Image Search Service" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"

:: Run the shortcut creation script
cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo.
echo CLIP Image Search has been registered to start automatically with Windows.
echo The service will run in the background without a console window.
echo To access the application, open http://localhost:8000 in your browser.
echo.
echo To remove from startup:
echo 1. Press Win+R
echo 2. Type 'shell:startup'
echo 3. Delete 'CLIP_Image_Search.lnk'
echo.
pause 