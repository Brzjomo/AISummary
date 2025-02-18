import requests
import os
import re
from pydub import AudioSegment

# TTS服务的配置
host = "192.168.50.238"
voices_url = "http://" + host + ":8774/voices"
base_url = "http://" + host + ":8774/forward"

# 获取可用的语音列表
response = requests.get(voices_url)

if response.status_code == 200:
    data = response.json()
    print("TTS服务测试成功")
else:
    print(f"获取语音列表失败: {response.status_code}")

# 用户输入文件路径
file_path = input("请输入文本文件的路径: ")

# 检查文件是否存在
if not os.path.exists(file_path):
    print(f"文件不存在: {file_path}")
    exit()

# 读取文本文件内容
with open(file_path, "r", encoding="utf-8") as file:
    input_text = file.read().strip()  # 读取文件内容并去除首尾空白字符

# 按句子拆分文本（按句号、感叹号、问号拆分）
sentences = re.split(r"(。|！|？)", input_text)  # 拆分后保留标点符号
sentences = ["".join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2)]  # 重新组合标点符号
sentences = [s for s in sentences if s]  # 去除空字符串
print(f"拆分后的句子列表: {sentences}")

# TTS请求参数
speed = "50"
volume = "50"
pitch = "50"
voice = "bdetts_xiao-chen-duo-yu-yan"

# 获取输入文件的名称（不带扩展名）
file_name = os.path.splitext(os.path.basename(file_path))[0]

# 临时保存每个句子的音频文件
temp_audio_files = []
for index, sentence in enumerate(sentences):
    # 构造请求URL
    request_url = base_url + "?text=" + sentence + "&speed=" + speed + "&volume=" + volume + "&pitch=" + pitch + "&voice=" + voice
    print(f"请求 {index + 1} 的地址: {request_url}")

    # 发送GET请求获取音频数据
    response = requests.get(request_url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 保存临时音频文件
        temp_file = f"temp_{index + 1}.mp3"
        with open(temp_file, "wb") as audio_file:
            audio_file.write(response.content)
        print(f"音频文件已保存为: {temp_file}")
        temp_audio_files.append(temp_file)
    else:
        print(f"获取音频失败: {response.status_code}")

# 合并所有音频文件
if temp_audio_files:
    combined_audio = AudioSegment.silent(duration=0)  # 初始化一个空的音频对象
    for temp_file in temp_audio_files:
        audio = AudioSegment.from_file(temp_file)
        combined_audio += audio  # 拼接音频
        os.remove(temp_file)  # 删除临时文件

    # 保存合并后的音频文件
    output_audio_file = f"{file_name}.mp3"
    combined_audio.export(output_audio_file, format="mp3")
    print(f"合并后的音频文件已保存为: {output_audio_file}")
else:
    print("没有可合并的音频文件")
