import requests
import time

# 节点测试端点配置
NODE_TEST_URL = 'http://localhost:3001/test/stop'

# 发送停止命令到节点测试端点
def send_stop_to_test_endpoint():
    try:
        response = requests.post(NODE_TEST_URL, timeout=5)
        print(f'发送停止命令到测试端点: {response.status_code}, {response.text}')
        return response.status_code == 200
    except Exception as e:
        print(f'发送请求失败: {str(e)}')
        return False

# 检查节点状态（通过心跳判断）
def check_node_heartbeat():
    # 这里简化处理，实际应用中可能需要查询服务端或直接检查节点日志
    print('请查看节点日志确认心跳是否恢复...')

# 主测试流程
def main():
    print('开始测试节点停止命令...')
    
    # 发送停止命令到测试端点
    if send_stop_to_test_endpoint():
        print('停止命令发送成功，等待节点响应...')
        time.sleep(3)
        check_node_heartbeat()
    else:
        print('停止命令发送失败')

if __name__ == '__main__':
    main()