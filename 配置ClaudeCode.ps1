# Claude Code 永久配置脚本 - APIKEY.FUN
# 右键选择"使用 PowerShell 运行"

$apiKey = "sk-7e494f62107b0321ed3628f4b8d153ded6f4f85f03d3ae006f1064db81f92c15"

Write-Host "正在配置 Claude Code 永久环境变量..." -ForegroundColor Cyan

[System.Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://api.apikey.fun", [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", $apiKey, [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1", [System.EnvironmentVariableTarget]::User)

Write-Host "✅ 永久环境变量配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "请重新打开 PowerShell 或 VS Code 终端，然后运行: claude" -ForegroundColor Yellow
Write-Host ""
Write-Host "验证命令: echo `$env:ANTHROPIC_BASE_URL" -ForegroundColor Gray
pause
