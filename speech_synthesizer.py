import configparser
from gradio_client import Client, handle_file

class SpeechSynthesizer:
    def __init__(self, config_file="config.ini"):
        self.config = self.load_config(config_file)
        self.client = Client(self.config["server_url"])

    def load_config(self, config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file, encoding="utf-8")
        cfg = parser["tts_config"]
        return {
            "server_url": cfg.get("server_url"),
            "ref_wav_path": cfg.get("ref_wav_path"),
            "prompt_text_path": cfg.get("prompt_text_path"),
            "prompt_language": cfg.get("prompt_language", "中文"),
            "text_language": cfg.get("text_language", "中文"),
            "how_to_cut": cfg.get("how_to_cut", "凑四句一切"),
            "top_k": cfg.getint("top_k", 15),
            "top_p": cfg.getfloat("top_p", 1.0),
            "temperature": cfg.getfloat("temperature", 1.0),
            "ref_free": cfg.getboolean("ref_free", False),
            "speed": cfg.getfloat("speed", 1.0),
            "if_freeze": cfg.getboolean("if_freeze", False),
            "inp_refs": cfg.get("inp_refs") or None,
            "sample_steps": cfg.getint("sample_steps", 32),
            "if_sr": cfg.getboolean("if_sr", False),
            "pause_second": cfg.getfloat("pause_second", 0.3),
            "api_name": cfg.get("api_name", "/get_tts_wav")
        }

    def _load_prompt_text(self):
        with open(self.config["prompt_text_path"], "r", encoding="utf-8") as f:
            return f.read().strip()

    def synthesize_single(self, text):
        prompt_text = self._load_prompt_text()

        result = self.client.predict(
            ref_wav_path=handle_file(self.config["ref_wav_path"]),
            prompt_text=prompt_text,
            prompt_language=self.config["prompt_language"],
            text=text,
            text_language=self.config["text_language"],
            how_to_cut=self.config["how_to_cut"],
            top_k=self.config["top_k"],
            top_p=self.config["top_p"],
            temperature=self.config["temperature"],
            ref_free=self.config["ref_free"],
            speed=self.config["speed"],
            if_freeze=self.config["if_freeze"],
            inp_refs=self.config["inp_refs"],
            sample_steps=self.config["sample_steps"],
            if_sr=self.config["if_sr"],
            pause_second=self.config["pause_second"],
            api_name=self.config["api_name"]
        )
        return result

    def synthesize_batch(self, text_list):
        """
        批量合成语音，每个元素调用一次 synthesize_single
        返回值是结果列表
        """
        results = []
        for idx, text in enumerate(text_list):
            print(f"[{idx+1}/{len(text_list)}] 正在合成：{text[:30]}...")
            try:
                result = self.synthesize_single(text)
                results.append(result)
            except Exception as e:
                print(f"合成失败：{e}")
                results.append(None)
        return results

if __name__ == "__main__":
    synthesizer = SpeechSynthesizer("config.ini")

    # 单句合成
    result = synthesizer.synthesize_single("民生银行在八闽大地持续创新服务...")
    print(result)

    # 批量合成
    batch = [
        "我们要以消费者为中心，构建本地化的服务体系。",
        "推动福建经济发展，是我们的责任。",
        "共建美好未来。"
    ]
    results = synthesizer.synthesize_batch(batch)
    for i, r in enumerate(results):
        print(f"第{i+1}条合成结果: {r}")

