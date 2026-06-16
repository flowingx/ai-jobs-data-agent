# 需要以管理员身份运行
# 右键点击此文件 -> 以管理员身份运行 PowerShell

$llamaPath = "C:\Users\flow\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"

Write-Host "=== 防火墙规则配置 ===" -ForegroundColor Cyan
Write-Host ""

# 删除现有规则
Write-Host "删除旧规则..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "llama-server.exe" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "llama-server (Inbound)" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "llama-server (Outbound)" -ErrorAction SilentlyContinue

# 添加入站允许规则
Write-Host "添加入站允许规则..." -ForegroundColor Green
New-NetFirewallRule -DisplayName "llama-server (Inbound)" `
    -Direction Inbound `
    -Action Allow `
    -Program $llamaPath `
    -Enabled True `
    -Profile Any `
    -Description "Allow llama-server inbound connections for local LLM inference on port 8080"

# 添加出站允许规则
Write-Host "添加出站允许规则..." -ForegroundColor Green
New-NetFirewallRule -DisplayName "llama-server (Outbound)" `
    -Direction Outbound `
    -Action Allow `
    -Program $llamaPath `
    -Enabled True `
    -Profile Any `
    -Description "Allow llama-server outbound connections for local LLM inference"

Write-Host ""
Write-Host "=== 验证规则 ===" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "llama-server*" | Format-Table DisplayName, Direction, Action, Enabled -AutoSize

Write-Host ""
Write-Host "防火墙规则配置完成！" -ForegroundColor Green
Write-Host "llama-server 现在可以通过端口 8080 访问" -ForegroundColor Green
