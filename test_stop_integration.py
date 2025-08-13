import requests
import time

# 配置信息
BASE_URL = 'http://localhost:2002'  # 服务端运行在本地2002端口
NODE_ID = 1
import sys

# 从命令行参数获取管理员密码
if len(sys.argv) > 1:
    ADMIN_PASS = sys.argv[1]
else:
    ADMIN_PASS = 'default_password'  # 默认密码，实际运行时应通过命令行参数提供

# 创建会话对象
session = requests.Session()

# 登录获取会话
def login():
    login_url = f'{BASE_URL}/web_api/login'
    data = {'username': 'admin', 'password': ADMIN_PASS}
    print(f'发送登录请求: {login_url}, 数据: {data}')
    response = session.post(login_url, json=data)
    print(f'登录响应状态码: {response.status_code}')
    print(f'登录响应头: {response.headers}')
    print(f'登录响应内容: {response.text}')
    if response.status_code == 200:
        print('登录成功')
        print(f'会话Cookie: {session.cookies.get_dict()}')
        return True
    else:
        print(f'登录失败: {response.status_code}, {response.text}')
        return False

# 触发节点运行任务
def trigger_node_run():
    trigger_url = f'{BASE_URL}/web_api/nodes/{NODE_ID}/trigger'
    response = session.post(trigger_url)
    print(f'触发运行指令: {response.status_code}, {response.text}')
    return response.status_code == 200

# 发送停止指令
def send_stop_command():
    stop_url = f'{BASE_URL}/web_api/nodes/{NODE_ID}/stop'
    response = session.post(stop_url)
    print(f'发送停止指令: {response.status_code}, {response.text}')
    return response.status_code == 200

# 检查节点状态
def check_node_status():
    status_url = f'{BASE_URL}/web_api/nodes'
    response = session.get(status_url)
    if response.status_code == 200:
        nodes = response.json()
        for node in nodes:
            if node['id'] == NODE_ID:
                print(f'节点状态: {node['status']}, 活动状态: {node['activity_status']}')
                return node
    print(f'获取节点状态失败: {response.status_code}, {response.text}')
    return None

# 主测试流程
def main():
    # 登录
    if not login():
        return

    # 检查初始状态
    print('初始状态:')
    check_node_status()

    # 触发运行任务
    if trigger_node_run():
        # 等待任务开始运行
        time.sleep(5)
        print('运行中状态:')
        check_node_status()

        # 发送停止指令
        if send_stop_command():
            # 等待停止指令生效
            time.sleep(5)
            print('停止后状态:')
            check_node_status()

if __name__ == '__main__':
    main()