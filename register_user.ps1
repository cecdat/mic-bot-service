# 注册用户脚本
$body = 'username=admin&password=password&confirm_password=password'
$headers = @{"Content-Type" = "application/x-www-form-urlencoded"}

Write-Host 'Attempting to register user...'
$response = Invoke-WebRequest -Uri 'http://10.52.175.75:5001/register' -Method Post -Body $body -Headers $headers -UseBasicParsing

Write-Host 'Registration response status code:' $response.StatusCode
Write-Host 'Registration response content:' $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length))