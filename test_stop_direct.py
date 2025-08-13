import requests

# 直接向节点发送停止命令
def send_stop_command():
    # 节点测试端点通常不进行严格认证
    stop_url = 'http://localhost:3001/stop'
    try:
        response = requests.post(stop_url)
        print(f'Stop command status code: {response.status_code}')
        print(f'Stop command content: {response.text}')
        return response
    except Exception as e:
        print(f'发送停止命令时出错: {e}')
        return None

# 主函数
def main():
    print('开始测试直接发送停止命令...')
    send_stop_command()
    print('测试完成，请查看节点日志确认结果')

if __name__ == '__main__':
    main()