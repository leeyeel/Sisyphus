import openai
import configparser
import time
import argparse

API_KEY=""
BASE_URL=""

def load_config(config_file="config.ini"):
    """
    加载配置文件，并设置 OpenAI 的 api_key 和 base_url
    """
    global API_KEY
    global BASE_URL
    config = configparser.ConfigParser()
    config.read(config_file)
    if "openai" not in config or "api_key" not in config["openai"]:
        raise Exception("配置文件中缺少 [openai] 节或 api_key 配置")
    
    API_KEY = config["openai"]["api_key"]
    
    # 如果配置文件中有 base_url，则设置，否则使用默认值
    if "base_url" in config["openai"]:
        BASE_URL = config["openai"]["base_url"]

def parse_srt_file(file_path):
    """
    解析 SRT 文件，将文件内容按空行拆分为多个字幕块。
    每个字幕块格式：
      1. 字幕编号（第一行）
      2. 时间戳行（第二行，格式如 "00:00:01,000 --> 00:00:04,000"）
      3. 一个或多行字幕文本
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    blocks_raw = content.split("\n\n")
    blocks = []
    for block in blocks_raw:
        lines = block.splitlines()
        if len(lines) >= 3:
            identifier = lines[0].strip()
            timestamp = lines[1].strip()
            text_lines = [line.strip() for line in lines[2:]]
            blocks.append({
                "identifier": identifier,
                "timestamp": timestamp,
                "text": text_lines
            })
    return blocks

def write_srt_file(blocks, file_path):
    """
    将字幕块列表写入 SRT 文件，保持 SRT 格式。
    """
    with open(file_path, "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(block["identifier"] + "\n")
            f.write(block["timestamp"] + "\n")
            for text_line in block["text"]:
                f.write(text_line + "\n")
            f.write("\n")

def merge_subtitles(blocks, merge_window=3):
    """
    将相邻的多个字幕块合并为一组，便于上下文翻译。
    
    参数:
      blocks: 原始字幕块列表
      merge_window: 每组合并的字幕块数量（例如 3 个）
    
    返回:
      merged_groups: 每个元素为字典，包含两个字段：
         - "blocks": 合并前的字幕块列表
         - "merged_text": 各块文本合并后，用特殊分隔符隔开的字符串
    """
    merged_groups = []
    i = 0
    delimiter = "|||"
    while i < len(blocks):
        group = blocks[i:i+merge_window]
        merged_texts = []
        for block in group:
            # 将每个字幕块内的多行文本合并成一句
            text_line = " ".join(block["text"]).strip()
            merged_texts.append(text_line)
        # 用特殊分隔符将各个块拼接起来
        merged_text = delimiter.join(merged_texts)
        merged_groups.append({
            "blocks": group,
            "merged_text": merged_text
        })
        i += merge_window
    return merged_groups

def translate_merged_text(client, merged_text):
    """
    使用 ChatGPT API 对合并后的字幕组文本进行翻译。
    提示中要求严格保留分隔符 "|||"，以便后续拆分得到与原组内字幕块数量一致的翻译结果。
    """
    delimiter = "|||"
    prompt = (
        f"请将下面的文本翻译为中文，确保在原始文本中的每个'{delimiter}'翻译后仍保留一个'{delimiter}'。"
        "如果需要合并或拆分句子以符合中文表达习惯，请在翻译后确保分隔符数量与原始一致。"
        "仅返回翻译后的文本，不要添加其他内容。\n\n"
        f"{merged_text}"
    )
    try:
        response = client.chat.completions.create(
            model="qwen-long-latest",
            messages=[
                {"role": "system", "content": "你是一个翻译助手，帮助用户将英文字幕翻译为中文，同时保留分隔符以便后续拆分。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
    except Exception as e:
        print("调用 OpenAI API 出错:", e)
        raise e

    translated_text = response.choices[0].message.content.strip()

    return translated_text

def main(input_file = 'en.srt', output_file = 'translated.srt'):
    global API_KEY
    global BASE_URL
    load_config()
    client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
    # 解析 SRT 文件
    blocks = parse_srt_file(input_file)
    print(f"检测到 {len(blocks)} 个字幕块。")

    # 合并字幕块，设置每组合并的块数（可根据需要调整）
    merge_window = 3
    merged_groups = merge_subtitles(blocks, merge_window=merge_window)
    print(f"合并成 {len(merged_groups)} 组字幕进行翻译。")
    delimiter = "|||"

    # 对每一组合并的字幕进行翻译
    for idx, group in enumerate(merged_groups):
        print(f"正在翻译第 {idx+1} 组字幕...")
        merged_text = group["merged_text"]
        translated_merged = translate_merged_text(client, merged_text)
        # 根据分隔符拆分翻译结果
        translated_segments = [seg.strip() for seg in translated_merged.split(delimiter)]
        num_original = len(group["blocks"])
        if len(translated_segments) != num_original:
            print(f"警告：翻译结果的分段数量({len(translated_segments)})与原始字幕块数量({num_original})不一致。")
            # 回退策略：若拆分数量不一致，则简单将整个翻译结果复制给各个块
            translated_segments = [translated_merged] * num_original
        # 将翻译结果回填到对应的字幕块中（此处每个字幕块仅显示一行翻译结果）
        for i, block in enumerate(group["blocks"]):
            block["text"] = [translated_segments[i]]
        # 为避免 API 调用频率过高，暂停 1 秒
        time.sleep(1)
    
    # 写入新的 SRT 文件，字幕块编号与时间戳保持不变
    write_srt_file(blocks, output_file)
    print(f"翻译完成，输出文件已生成：{output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 GPT 翻译 SRT 字幕文件")
    parser.add_argument("--input", "-i", type=str, help="输入的 SRT 文件", default="input.srt")
    parser.add_argument("--output", "-o", type=str, help="输出的翻译 SRT 文件", default="translated_output.srt")
    args = parser.parse_args()
    main(args.input, args.output)

