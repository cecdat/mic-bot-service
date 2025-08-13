import requests
import time

# 测试根端点连接
def test_root_endpoint():
    url = 'http://localhost:3001/'
    try:
        response = requests.get(url, timeout=5)
        print(f'状态码: {response.status_code}')
        print(f'响应内容: {response.text}')
        return True
    except Exception as e:
        print(f'请求失败: {str(e)}')
        return False

# 连续测试5次，每次间隔2秒
print('开始测试根端点连接...')
success_count = 0
for i in range(5):
    print(f'测试 #{i+1}')
    if test_root_endpoint():
        success_count += 1
    time.sleep(2)

print(f'测试完成。成功次数: {success_count}/5')