import requests

# 先登录获取会话
login_url = 'http://localhost:2002/web_api/login'
login_data = {'username': 'admin', 'password': 'password'}
login_response = requests.post(login_url, json=login_data)
print(f'Login status code: {login_response.status_code}')
print(f'Login content: {login_response.text}')

# 获取会话cookie
cookies = login_response.cookies

# 使用会话触发节点命令
trigger_url = 'http://localhost:2002/web_api/nodes/1/trigger'
headers = {'Content-Type': 'application/json'}
trigger_response = requests.post(trigger_url, headers=headers, json={}, cookies=cookies)
print(f'Trigger status code: {trigger_response.status_code}')
print(f'Trigger content: {trigger_response.text}')