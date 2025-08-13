import requests
import time

# 节点测试端点配置
NODE_TEST_URL = 'http://localhost:3001/test/stop'  # 假设节点测试端点在3001端口

# 发送停止指令到节点测试端点
def send_stop_command_direct():
    try:
        print(f'发送停止指令到节点测试端点: {NODE_TEST_URL}')
        response = requests.post(NODE_TEST_URL, timeout=10)
        print(f'停止指令响应状态码: {response.status_code}')
        print(f'停止指令响应内容: {response.text}')
        return response.status_code == 200
    except Exception as e:
        print(f'发送请求失败: {e}')
        return False

# 检查节点状态（模拟函数，实际应用中可能需要不同的实现）
def check_node_status():
    # 这里只是模拟检查节点状态，实际应用中可能需要访问节点的状态端点
    print('检查节点状态: 假设节点已停止任务，状态为Idle')
    return {'status': 'Online', 'activity_status': 'Idle'}

# 主测试流程
def main():
    print('开始测试节点停止指令...')

    # 发送停止指令
    if send_stop_command_direct():
        # 等待停止指令生效
        time.sleep(3)
        print('停止后状态:')
        check_node_status()
    else:
        print('发送停止指令失败')

if __name__ == '__main__':
    main()