@echo off
echo === Configuring Firewall Rules for llama-server ===
echo.

set LLAMA_PATH=C:\Users\flow\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe

echo Removing existing rules...
netsh advfirewall firewall delete rule name="llama-server.exe" >nul 2>&1
netsh advfirewall firewall delete rule name="llama-server (Inbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="llama-server (Outbound)" >nul 2>&1

echo Adding inbound allow rule...
netsh advfirewall firewall add rule name="llama-server (Inbound)" dir=in action=allow program="%LLAMA_PATH%" enable=yes profile=any

echo Adding outbound allow rule...
netsh advfirewall firewall add rule name="llama-server (Outbound)" dir=out action=allow program="%LLAMA_PATH%" enable=yes profile=any

echo.
echo === Verifying Rules ===
netsh advfirewall firewall show rule name="llama-server (Inbound)"
netsh advfirewall firewall show rule name="llama-server (Outbound)"

echo.
echo Done! Press any key to exit...
pause >nul
