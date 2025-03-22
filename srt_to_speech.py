import os
import srt
import datetime
from pydub import AudioSegment
from speech_synthesizer import SpeechSynthesizer  # 你之前封装好的类

class SRTToSpeech:
    def __init__(self, srt_path, output_dir, config_file="config.ini"):
        self.srt_path = srt_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.tts = SpeechSynthesizer(config_file=config_file)
        self.char_per_sec = 2.5
        self.speed_min = 0.7
        self.speed_max = 1.5

    def parse_srt(self):
        with open(self.srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        return list(srt.parse(srt_content))

    def estimate_duration(self, text):
        return len(text.strip()) / self.char_per_sec

    def to_milliseconds(self, td: datetime.timedelta):
        return int(td.total_seconds() * 1000)

    def generate_segments(self):
        subtitles = self.parse_srt()
        all_segments = []

        for i, item in enumerate(subtitles):
            target_duration = self.to_milliseconds(item.end - item.start)
            estimated_duration = self.estimate_duration(item.content)
            speed = estimated_duration / (target_duration / 1000)

            # 限制语速范围
            speed = max(self.speed_min, min(speed, self.speed_max))
            print(f"[{i+1}/{len(subtitles)}] 生成语音：{item.content.strip()} (目标: {target_duration}ms, 速度: {speed:.2f})")

            # 合成语音
            try:
                self.tts.config["speed"] = speed
                audio_path = os.path.join(self.output_dir, f"segment_{i+1:04d}.wav")
                result = self.tts.synthesize_single(item.content)
                
                # 保存结果（假设 result 是 AudioSegment 或文件路径）
                if isinstance(result, AudioSegment):
                    audio = result
                else:
                    audio = AudioSegment.from_file(result)

                audio.export(audio_path, format="wav")
                actual_duration = len(audio)
            except Exception as e:
                print(f"❌ 合成失败: {e}")
                audio_path = None
                actual_duration = 0

            all_segments.append({
                "start": self.to_milliseconds(item.start),
                "end": self.to_milliseconds(item.end),
                "path": audio_path,
                "duration": actual_duration
            })

        return all_segments

    def assemble_audio(self, segments, final_output_path):
        full_audio = AudioSegment.silent(duration=0)
        current_time = 0

        for seg in segments:
            gap = seg["start"] - current_time
            if gap > 0:
                print(f"插入静音 {gap}ms")
                full_audio += AudioSegment.silent(duration=gap)
                current_time += gap

            if seg["path"] and os.path.exists(seg["path"]):
                audio = AudioSegment.from_wav(seg["path"])
                full_audio += audio
                current_time += len(audio)
            else:
                print("跳过无效段")

        full_audio.export(final_output_path, format="wav")
        print(f"✅ 合成完成，保存至：{final_output_path}")

    def run(self, final_output="output.wav"):
        segments = self.generate_segments()
        final_path = os.path.join(self.output_dir, final_output)
        self.assemble_audio(segments, final_path)

if __name__ == "__main__":
    converter = SRTToSpeech(
        srt_path="chapter1.srt",
        output_dir="./tts_segments",
        config_file="config.ini"
    )
    converter.run("final_output.wav")

