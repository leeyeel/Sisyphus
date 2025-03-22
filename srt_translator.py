import openai
import configparser
import argparse

class SRTTranslator:
    def __init__(self, model_type="qwen", config_file="config.ini"):
        self.config_file = config_file
        self.model_type = model_type
        self.model_name, self.api_key, self.base_url, self.prompts = self.load_config()

    def load_config(self):
        """
        加载配置文件，并设置 OpenAI 的 api_key 和 base_url
        """
        config = configparser.ConfigParser()
        config.read(self.config_file)
        model_name = config[self.model_type]["model_name"]
        api_key = config[self.model_type]["api_key"]
        base_url = config[self.model_type]["base_url"]
        prompts = config[self.model_type]["prompts"]
        return model_name, api_key, base_url, prompts

    def translate(self, prompt, src_text):
        """
        使用 OpenAI API 翻译字幕文本
        """
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": (
                        "以下是一份英文字幕文件(.srt)内容，"
                        "请按照上述要求进行翻译。翻译完成后，"
                        "请输出新的字幕文件内容（保持字幕序号、时间轴，并根据需要合理调整）。"
                        f":\n\n{src_text}"
                    )}
                ],
                temperature=0.1,
            )
        except Exception as e:
            print("调用 OpenAI API 出错:", e)
            raise e

        return response.choices[0].message.content.strip()

    def translate_file(self, input_file, output_file):
        """
        翻译输入文件内容并保存为输出文件
        """
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        translated_text = self.translate(self.prompts, content)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(translated_text)
        print(f"翻译完成，输出文件已生成：{output_file}")
        return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 GPT 翻译 SRT 字幕文件")
    parser.add_argument("--input", "-i", type=str, help="输入的 SRT 文件", default="input.srt")
    parser.add_argument("--output", "-o", type=str, help="输出的翻译 SRT 文件", default="translated_output.srt")
    parser.add_argument("--model_type", "-m", type=str, help="使用的模型类型（如 openai 或 qwen）", default="qwen")
    args = parser.parse_args()

    translator = SRTTranslator(model_type=args.model_type)
    translator.translate_file(args.input, args.output)

