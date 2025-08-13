import requests
import time
import sys

# 配置
NODE_STOP_ENDPOINT = 'http://localhost:3001/test/stop'  # 节点停止端点
NODE_COMMAND_ENDPOINT = 'http://localhost:3001/test/run_tasks'  # 任务触发端点
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟(秒)

# 发送请求函数（带重试）
def send_request(url, method='GET', json_data=None):
    for attempt in range(1, MAX_RETRIES + 1):
        print(f'尝试 {attempt}/{MAX_RETRIES}')
        try:
            print(f'发送{method}请求到: {url}')
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=json_data, timeout=10)
            print(f'响应状态码: {response.status_code}')
            print(f'响应内容: {response.text}')
            return response
        except Exception as e:
            print(f'发送请求时发生错误: {str(e)}')
        if attempt < MAX_RETRIES:
            print(f'{RETRY_DELAY}秒后重试...')
            time.sleep(RETRY_DELAY)
    return None

# 触发节点执行任务
def trigger_node_tasks():
    print('尝试触发节点执行任务...')
    response = send_request(NODE_COMMAND_ENDPOINT, 'GET')
    if response and response.status_code == 200:
        print('成功触发节点任务')
        return True
    else:
        print('触发节点任务失败，将尝试直接发送停止指令')
        return False

# 发送停止指令
def send_stop_command():
    print('开始发送停止指令...')
    response = send_request(NODE_STOP_ENDPOINT)
    if response and response.status_code == 200:
        print('发送停止指令成功')
        return True
    else:
        print('发送停止指令失败')
        return False

# 检查节点日志(模拟函数)
def check_node_logs():
    print('提示: 请查看节点日志，确认是否收到并处理了停止指令')
    print('预期日志: 收到 [停止任务] 指令，正在终止当前任务...')

# 主测试流程
def main():
    print('开始测试节点停止指令...')
    
    # 尝试触发节点任务
    trigger_success = trigger_node_tasks()
    
    # 等待一段时间，确保任务开始执行
    if trigger_success:
        print('等待5秒，确保任务开始执行...')
        time.sleep(5)
    
    # 发送停止指令
    stop_success = send_stop_command()
    
    if stop_success:
        print('发送停止指令成功')
        # 等待停止指令生效
        time.sleep(3)
        check_node_logs()
    else:
        print('发送停止指令失败，已达到最大重试次数')
        print('可能的原因:')
        print('1. 节点服务未启动')
        print('2. 节点服务未监听3001端口')
        print('3. 网络连接问题')

if __name__ == '__main__':
    main()