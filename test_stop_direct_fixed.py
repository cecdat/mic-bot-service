import requests

# 直接向节点测试端点发送停止命令
try:
    response = requests.get('http://localhost:3001/test/stop')
    if response.status_code == 200:
        print('成功发送停止命令:', response.json())
    else:
        print(f'发送停止命令失败，状态码: {response.status_code}')
except Exception as e:
    print(f'发送停止命令时出错: {str(e)}')