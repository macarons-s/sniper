import requests
import time
import json
from datetime import datetime

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
date = input("预定日期：")

t1 = "08:20-09:10"
t2 = "09:10-10:00"
t3 = "10:10-11:00"
t4 = "11:00-11:50"
t5 = "14:00-14:50"
t6 = "14:50-15:40"
t7 = "15:50-16:40"
t8 = "16:40-17:30"
# 定义优先时段列表###############################
priority_timeslots = [t6, t5, t7, t8, t3, t2, t4, t1]

# 请求体
data = {
    "depId": "4003",  # 科室 ID
    "doctorId": "6060",  # 医生 ID
    "date": f"2025-{date}",  # 挂号日期
    "type": 2,  # 挂号类型
}
print(data["date"])
t = []
first_run = True
proxies = {
    "http": "",
    "https": "",
}
# 目标 URL 和请求头
url = "https://ih-applet.xajwzx.com/gateway/his-plan/doctor-order-source-list"
headers = {
    "Authorization": config["Authorization"],
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",  # 需要替换为你的 User-Agent
    "Referer": "......",
}

last_push_time = None
def push_to_wechat():
    global last_push_time
    now = datetime.now()
    if last_push_time and (now - last_push_time).total_seconds() < 3600:
        return
    url = f'https://sctapi.ftqq.com/{config["push_key"]}.send'
    data = {
        "title": "有可用号源！",
        "desp": "有可用号源！脚本可能已经自动锁定号源，请查看",
    }
    try:
        requests.post(url, data=data, proxies=proxies, timeout=10)
    except requests.RequestException as e:
        print("推送失败：", e)
        return
    last_push_time = now
    return

def book_appointment(tt, serialNo, masterId):
    url2 = "https://ih-applet.xajwzx.com/gateway/his-order/confirm"
    headers2 = {
        "Authorization": config["Authorization"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
        "Content-Type": "application/json",
    }

    data2 = {
        "cardNo": config["cardNo"],
        "deptId": data["depId"],
        "deptName": "心理科",
        "doctorId": data["doctorId"],
        "doctorName": "姜华东",
        "masterId": masterId,
        "orderDate": data["date"],
        "patientCode": config["patientCode"],
        "type": 2,
        "startTime": tt[:5],
        "endTime": tt[-5:],
        "serialNo": serialNo,
        "cost": "8",
        "payWay": 0,
        "clinicLabel": "",
    }
    print(serialNo)
    for _ in range(10):
        response = requests.post(url2, headers=headers2, json=data2, proxies=proxies)
        print(response.json())
        if response.status_code == 200:
            return True
        time.sleep(1)
    print("发起订单失败")
    return False


# 检查是否有号源
def check_availability():
    start_time = time.time()
    # 发送请求
    response = requests.post(url, headers=headers, json=data, proxies=proxies)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"请求耗时：{elapsed_time:.2f} 秒")
    if response.status_code == 200:
        response_json = response.json()
        available_slots = (
            response_json["data"]["morning"] + response_json["data"]["afternoon"]
        )
        print("号源列表请求" + response_json["msg"], response_json["timestamp"])
        global first_run
        if first_run:
            print(available_slots)
            first_run = False
        # 遍历所有时段，检查优先时段
        for t in priority_timeslots:
            for slot in available_slots:
                time_interval = slot["timeinterval"]
                if t == time_interval and slot["clinicLabelData"][0]["num"] > 0:
                    serialNo = slot["clinicLabelData"][0]["clinicData"][0]["serialNo"]
                    masterid = slot["clinicLabelData"][0]["clinicData"][0]["masterid"]
                    print(f"优先指定号源可用: {time_interval}")
                    push_to_wechat()
                    return book_appointment(t, serialNo, masterid)
    else:
        print("请求失败:", response)
    return False


def main():
    loop = 1
    while True:
        print(f"\n第{loop}次请求")
        loop += 1
        if check_availability():
            break  # 如果找到可用号源，停止循环
        print("5 秒钟后重试...")
        time.sleep(5)  # 每 5 秒钟检查一次


if __name__ == "__main__":
    main()
    while input("输入q退出...") != "q":
        pass
