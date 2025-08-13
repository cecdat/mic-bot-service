import requests
import time

# 登录函数
def login():
    login_url = 'http://localhost:2002/web_api/login'
    login_data = {'username': 'admin', 'password': 'password'}
    login_response = requests.post(login_url, json=login_data)
    print(f'Login status code: {login_response.status_code}')
    print(f'Login content: {login_response.text}')
    return login_response.cookies if login_response.status_code == 200 else None

# 触发运行命令
def trigger_run(cookies):
    trigger_url = 'http://localhost:2002/web_api/nodes/1/trigger'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(trigger_url, headers=headers, json={}, cookies=cookies)
    print(f'Trigger RUN status code: {response.status_code}')
    print(f'Trigger RUN content: {response.text}')
    return response

# 触发停止命令
def trigger_stop(cookies):
    stop_url = 'http://localhost:2002/web_api/nodes/1/stop'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(stop_url, headers=headers, json={}, cookies=cookies)
    print(f'Trigger STOP status code: {response.status_code}')
    print(f'Trigger STOP content: {response.text}')
    return response

# 获取节点状态
def get_node_status(cookies):
    status_url = 'http://localhost:2002/web_api/nodes/1'
    headers = {'Content-Type': 'application/json'}
    response = requests.get(status_url, headers=headers, cookies=cookies)
    print(f'Get status code: {response.status_code}')
    print(f'Get status content: {response.text}')
    return response.json() if response.status_code == 200 else None

# 主测试函数
def main():
    print('开始测试异步处理功能...')
    # 1. 登录获取会话
    cookies = login()
    if not cookies:
        print('登录失败，无法继续测试')
        return

    # 2. 获取初始状态
    initial_status = get_node_status(cookies)
    print(f'初始状态: {initial_status}')

    # 3. 触发运行命令
    trigger_run(cookies)
    print('已发送运行命令，等待10秒让任务开始执行...')
    time.sleep(10)

    # 4. 检查运行状态
    running_status = get_node_status(cookies)
    print(f'运行中状态: {running_status}')

    # 5. 触发停止命令
    print('发送停止命令...')
    trigger_stop(cookies)
    print('已发送停止命令，等待5秒让命令生效...')
    time.sleep(5)

    # 6. 检查停止后状态
    final_status = get_node_status(cookies)
    print(f'停止后状态: {final_status}')

    print('测试完成，请查看节点日志确认结果')

if __name__ == '__main__':
    main()