import openai
import configparser
import argparse

def load_config(model_type = "openai", config_file="config.ini"):
    """
    加载配置文件，并设置 OpenAI 的 api_key 和 base_url
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    model_name = config[model_type]["model_name"]
    api_key = config[model_type]["api_key"]
    base_url = config[model_type]["base_url"]
    return model_name, api_key,base_url

def translate_srt(api_key, base_url, model_name, src_text):
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
                model= model_name,
                messages=[
                    {"role": "system", "content": f"你是一位专业的字幕翻译助手。\
                            你的任务是将给定的英文字幕文件翻译成中文，\
                            并根据给定的要求输出翻译后的字幕文件。\
                            你需要：\
                            1. 尽可能保持原来的时间轴（start time、end time），\
                            但如翻译后句子数目有增减，需要合理地合并或拆分字幕，\
                            并对时间轴做相应调整。\
                            2. 翻译时要联系上下文，不要孤立的对某条字幕直译。\
                            确保疑问上下流畅，语义完整，不要出现突兀的语句。\
                            3. 每个字幕序号尽量与原来英文字幕一一对应，\
                            如果某个句子不适合一一对应，则可以进行拆分，\
                            但只能在有标点符号（逗号、句号、问号等）处或语气停顿处拆分断句。\
                            4. 最终输出的字幕应为完整的 `.srt` 格式（或与原字幕文件相同的格式），\
                            包括字幕序号、时间轴和中文翻译后的文本, 除这些内容外不要包含其他内容。"},
                    {"role": "user", "content": f"以下是一份英文字幕文件(.srt)内容，\
                            请按照上述要求进行翻译。翻译完成后，\
                            请输出新的字幕文件内容（保持字幕序号、时间轴，并根据需要合理调整）。\
                            :\n\n{src_text}"}
                    ],
                temperature = 0.1,
                )
    except Exception as e:
        print("调用 OpenAI API 出错:", e)
        raise e

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 GPT 翻译 SRT 字幕文件")
    parser.add_argument("--input", "-i", type=str, help="输入的 SRT 文件", default="input.srt")
    parser.add_argument("--output", "-o", type=str, help="输出的翻译 SRT 文件", default="translated_output.srt")
    args = parser.parse_args()
    model_name, api_key, base_url = load_config('qwen')
    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read().strip()
    translated_text = translate_srt(api_key, base_url, model_name, content)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(translated_text)

    print(f"翻译完成，输出文件已生成：{args.output}")


