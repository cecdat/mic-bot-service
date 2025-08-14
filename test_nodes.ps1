$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Write-Host 'Attempting to login...'
# 创建表单数据
$form = @{username='admin';password='password'}
# 提交登录请求，允许重定向
$loginResponse = Invoke-WebRequest -Uri 'http://10.52.175.75:5001/login' -Method Post -Body $form -WebSession $session -UseBasicParsing -MaximumRedirection 5
Write-Host 'Login response status code:' $loginResponse.StatusCode
Write-Host 'Login response final URI:' $loginResponse.BaseResponse.ResponseUri
Write-Host 'Login response content length:' $loginResponse.Content.Length

# 显示Cookie信息
Write-Host 'Session cookies after login:'
$session.Cookies.GetCookies('http://10.52.175.75:5001/') | ForEach-Object {
    Write-Host "  - $($_.Name): $($_.Value)"
}

Write-Host 'Checking if logged in...'
$testResponse = Invoke-WebRequest -Uri 'http://10.52.175.75:5001/' -Method Get -WebSession $session -UseBasicParsing
Write-Host 'Test response status code:' $testResponse.StatusCode
Write-Host 'Test response final URI:' $testResponse.BaseResponse.ResponseUri
Write-Host 'Test response content preview:' $testResponse.Content.Substring(0, [Math]::Min(200, $testResponse.Content.Length))

Write-Host 'Requesting nodes list...'
try {
    $nodesResponse = Invoke-WebRequest -Uri 'http://10.52.175.75:5001/web_api/nodes' -Method Get -WebSession $session -UseBasicParsing
    Write-Host 'Nodes response status code:' $nodesResponse.StatusCode
    Write-Host 'Nodes response content:' $nodesResponse.Content
} catch {
    Write-Host 'Error requesting nodes list:'
    Write-Host 'Status code:' $_.Exception.Response.StatusCode
    Write-Host 'Message:' $_.Exception.Message
}