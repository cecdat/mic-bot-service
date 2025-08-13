import requests
import time

# 创建模拟登录会话
def create_session():
    # 创建一个会话
    session = requests.Session()
    # 手动设置session cookie，模拟登录成功
    # 注意：这里的cookie名称和值需要与实际应用匹配
    # 根据auth.py，我们需要设置一个包含user_id的会话
    # 由于无法访问实际数据库，我们假设user_id为1
    session.cookies.set('session', 'dummy_session_value')
    print('已创建模拟登录会话')
    return session

# 触发运行命令
def trigger_run(session):
    trigger_url = 'http://localhost:2002/web_api/nodes/1/trigger'
    headers = {'Content-Type': 'application/json'}
    response = session.post(trigger_url, headers=headers, json={})
    print(f'Trigger RUN status code: {response.status_code}')
    print(f'Trigger RUN content: {response.text}')
    return response

# 触发停止命令
def trigger_stop(session):
    stop_url = 'http://localhost:2002/web_api/nodes/1/stop'
    headers = {'Content-Type': 'application/json'}
    response = session.post(stop_url, headers=headers, json={})
    print(f'Trigger STOP status code: {response.status_code}')
    print(f'Trigger STOP content: {response.text}')
    return response

# 主测试函数
def main():
    print('开始测试异步处理功能...')
    # 1. 创建模拟登录会话
    session = create_session()

    # 2. 触发运行命令
    trigger_run(session)
    print('已发送运行命令，等待5秒让任务开始执行...')
    time.sleep(5)

    # 3. 触发停止命令
    print('发送停止命令...')
    trigger_stop(session)
    print('测试完成，请查看节点日志确认结果')

if __name__ == '__main__':
    main()