import requests
import requests
import json

session = requests.Session()

def test_get_points():
    # 登录获取会话
    login_url = 'http://10.52.175.75:2002/web_api/login'
    login_data = {'username': 'admin', 'password': 'admin'}
    try:
        print(f'正在登录: {login_url}')
        login_response = session.post(login_url, json=login_data, timeout=10)
        print(f'登录状态码: {login_response.status_code}')
        print(f'登录响应: {login_response.text[:300]}...')
    except Exception as e:
        print(f'登录失败: {str(e)}')
        return

    # 请求get_points接口
    points_url = 'http://10.52.175.75:2002/web_api/get_points?filter=all'
    try:
        print(f'正在请求接口: {points_url}')
        points_response = session.get(points_url, timeout=10)
        print(f'接口状态码: {points_response.status_code}')
        print(f'接口响应: {points_response.text[:500]}...')
        try:
            data = points_response.json()
            print(f'返回数据量: {len(data)}')
            if len(data) > 0:
                print('返回数据示例:')
                print(json.dumps(data[0], indent=2, ensure_ascii=False)[:300] + '...')
        except json.JSONDecodeError:
            print('响应不是有效的JSON格式')
    except Exception as e:
        print(f'请求失败: {str(e)}')
        return

test_get_points()