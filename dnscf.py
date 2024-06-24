import requests
import traceback
import time
import os
import json

# API 密钥
CF_API_TOKEN    =   os.environ.get("CF_API_TOKEN")
CF_ZONE_ID      =   os.environ.get("CF_ZONE_ID")
CF_DNS_NAME     =   os.environ.get("CF_DNS_NAME")

# pushplus_token
PUSHPLUS_TOKEN  =   os.environ.get("PUSHPLUS_TOKEN")

headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            print(f"get_cf_speed_test_ip 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
    return None

def get_dns_records(name):
    def_info = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                def_info.append(record['id'])
        return def_info
    except Exception as e:
        print('获取 DNS 记录时出错:', e)
        return None

def update_dns_record(record_id, name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"DNS 记录更新成功: ---- 时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} ---- IP: {cf_ip}")
        return f"IP: {cf_ip} 解析 {name} 成功"
    except Exception as e:
        print(f"DNS 记录更新失败: ---- 时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} ---- 错误信息: {e}")
        return f"IP: {cf_ip} 解析 {name} 失败"

def push_plus(content):
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "IP 优选 DNS CF 推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=body, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"PushPlus 通知失败: {e}")

def main():
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("获取 IP 地址失败。")
        return
    
    ip_addresses = ip_addresses_str.split(',')
    dns_records = get_dns_records(CF_DNS_NAME)
    if not dns_records:
        print("获取 DNS 记录失败。")
        return
    
    print(f"获取到的 IP 地址数量: {len(ip_addresses)}")
    print(f"获取到的 DNS 记录数量: {len(dns_records)}")

    push_plus_content = []
    for index, ip_address in enumerate(ip_addresses):
        dns_index = index % len(dns_records)
        dns = update_dns_record(dns_records[dns_index], CF_DNS_NAME, ip_address)
        push_plus_content.append(dns)

    push_plus('\n'.join(push_plus_content))

if __name__ == '__main__':
    main()
