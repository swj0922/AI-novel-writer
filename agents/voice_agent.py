import dashscope
from dashscope.audio.tts_v2 import *
from datetime import datetime
import os
from pydub import AudioSegment

def get_timestamp():
    now = datetime.now()
    formatted_timestamp = now.strftime("[%Y-%m-%d %H:%M:%S.%f]")
    return formatted_timestamp

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def merge_audio_files(file_list, output_filename):
    combined_audio = AudioSegment.empty()
    for audio_file in file_list:
        combined_audio += AudioSegment.from_mp3(audio_file)
    combined_audio.export(output_filename, format="mp3")
    print(f"已合并音频文件到：{output_filename}")
    # 删除原始分段文件
    for audio_file in file_list:
        os.remove(audio_file)
        print(f"已删除分段文件：{audio_file}")


dashscope.api_key = "sk-1ef165b563f646a482c2a0b589fa9b09"

# 模型
model = "cosyvoice-v2"
# 音色
voice = "longmiao_v2"


# 定义回调接口
class Callback(ResultCallback):
    _player = None
    _stream = None

    def __init__(self, output_filename="output.mp3"):
        self.output_filename = output_filename

    def on_open(self):
        self.file = open(self.output_filename, "wb")
        print("连接建立：" + get_timestamp())

    def on_complete(self):
        print(f"语音合成完成，所有合成结果已被接收，文件保存为 {self.output_filename}：" + get_timestamp())

    def on_error(self, message: str):
        print(f"语音合成出现异常：{message}")

    def on_close(self):
        print("连接关闭：" + get_timestamp())
        self.file.close()

    def on_event(self, message):
        pass

    def on_data(self, data: bytes) -> None:
        print(get_timestamp() + " 二进制音频长度为：" + str(len(data)))
        self.file.write(data)


if __name__ == "__main__":
    chapter_files = [
        "Novel_Output/chapters/chapter_1.txt",
    ]

    for chapter_file in chapter_files:
        print(f"正在处理文件: {chapter_file}")
        chapter_content = read_file_content(chapter_file)
        
        # 从文件路径中提取文件名作为输出MP3文件名
        base_name = os.path.basename(chapter_file)
        output_base_name = os.path.splitext(base_name)[0]

        if len(chapter_content) > 1900:
            print(f"文本长度 ({len(chapter_content)}) 大于1900，将进行分割处理。")
            # 简单地将文本分割成两部分
            mid_point = len(chapter_content) // 2
            # 尝试在句子末尾分割，避免截断句子
            split_index = chapter_content.rfind('。', 0, mid_point) # 寻找第一个句号
            if split_index == -1: # 如果没有句号，就直接在中间分割
                split_index = mid_point
            else:
                split_index += 1 # 包含句号

            part1 = chapter_content[:split_index]
            part2 = chapter_content[split_index:]

            # 处理第一部分
            output_mp3_name_part1 = f"{output_base_name}_part1.mp3"
            callback_part1 = Callback(output_mp3_name_part1)
            synthesizer_part1 = SpeechSynthesizer(
                model=model,
                voice=voice,
                callback=callback_part1,
                speech_rate=0.95
            )
            synthesizer_part1.call(part1)
            print(f'[Metric] Part1 requestId为：{{}}，首包延迟为：{{}}毫秒'.format(
                synthesizer_part1.get_last_request_id(),
                synthesizer_part1.get_first_package_delay()))

            # 处理第二部分
            output_mp3_name_part2 = f"{output_base_name}_part2.mp3"
            callback_part2 = Callback(output_mp3_name_part2)
            synthesizer_part2 = SpeechSynthesizer(
                model=model,
                voice=voice,
                callback=callback_part2,
            )
            synthesizer_part2.call(part2)
            print(f'[Metric] Part2 requestId为：{{}}，首包延迟为：{{}}毫秒'.format(
                synthesizer_part2.get_last_request_id(),
                synthesizer_part2.get_first_package_delay()))
            
        else:
            print(f"文本长度 ({len(chapter_content)}) 小于等于1900，直接处理。")
            output_mp3_name = f"{output_base_name}.mp3"
            callback = Callback(output_mp3_name)

            synthesizer = SpeechSynthesizer(
                model=model,
                voice=voice,
                callback=callback,
            )

            synthesizer.call(chapter_content)
            print('[Metric] requestId为：{}，首包延迟为：{}毫秒'.format(
                synthesizer.get_last_request_id(),
                synthesizer.get_first_package_delay()))
        
        print("\n" + "="*50 + "\n") # 分隔不同章节的输出

# 要用列表记录哪些文件长度大于2000，最后统一合并
# 合并音频文件
#merged_output_name = f"{output_base_name}.mp3"
#merge_audio_files([output_mp3_name_part1, output_mp3_name_part2], merged_output_name)
