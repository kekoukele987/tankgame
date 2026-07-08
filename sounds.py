"""
音效管理模块
程序化生成全部音效和背景音乐，无需外部音频文件
使用 WAV 合成 → pygame.mixer.Sound
"""
import pygame
import math
import struct
import random


class SoundManager:
    """音效管理器（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 确保 mixer 已初始化
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        self.sounds = {}
        self.music_channel = None
        self.enabled = True
        self._bgm_playing = False

        self._generate_all()

    # ========== WAV 生成工具 ==========

    def _make_sound(self, samples, rate=22050):
        """将浮点采样列表 [-1, 1] 转为 pygame Sound"""
        n = len(samples)
        data_size = n * 2  # 16-bit mono
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + data_size,
            b'WAVE', b'fmt ',
            16,          # chunk size
            1,           # PCM
            1,           # mono
            rate,        # sample rate
            rate * 2,    # byte rate
            2,           # block align
            16,          # bits per sample
            b'data',
            data_size,
        )
        data = b''.join(
            struct.pack('<h', max(-32767, min(32767, int(s * 32767))))
            for s in samples
        )
        return pygame.mixer.Sound(buffer=header + data)

    def _add_sound(self, name, samples, rate=22050):
        """生成并注册一个音效"""
        sound = self._make_sound(samples, rate)
        self.sounds[name] = sound

    # ========== 音效生成 ==========

    def _square_wave(self, freq, t, harmonics=3):
        """方波近似（通过奇次谐波合成）"""
        val = 0.0
        for k in range(harmonics):
            h = 2 * k + 1
            val += math.sin(2 * math.pi * freq * h * t) / h
        return val

    def _noise_sample(self):
        """白噪声采样"""
        return random.uniform(-1, 1)

    def _gen_shoot(self):
        """射击音效 — 短促高频扫描"""
        rate = 22050
        duration = 0.08
        n = int(rate * duration)
        samples = []
        for i in range(n):
            t = i / rate
            progress = t / duration
            freq = 700 - 300 * progress
            val = self._square_wave(freq, t, harmonics=3)
            env = 1.0 - progress
            env = env * env  # 二次衰减
            samples.append(val * env * 0.4)
        self._add_sound('shoot', samples, rate)

    def _gen_enemy_shoot(self):
        """敌方射击 — 略低沉"""
        rate = 22050
        duration = 0.08
        n = int(rate * duration)
        samples = []
        for i in range(n):
            t = i / rate
            progress = t / duration
            freq = 450 - 200 * progress
            val = self._square_wave(freq, t, harmonics=3)
            env = (1.0 - progress) ** 2
            samples.append(val * env * 0.35)
        self._add_sound('enemy_shoot', samples, rate)

    def _gen_explosion(self):
        """爆炸 — 低频正弦 + 噪声"""
        rate = 22050
        duration = 0.4
        n = int(rate * duration)
        samples = []
        for i in range(n):
            t = i / rate
            progress = t / duration
            # 低频基音
            sine = math.sin(2 * math.pi * 80 * t) * 0.6
            # 噪声分量
            noise = self._noise_sample() * 0.4
            val = sine + noise
            # 衰减包络
            env = math.exp(-progress * 6)
            samples.append(val * env * 0.5)
        self._add_sound('explosion', samples, rate)

    def _gen_wall_hit(self):
        """墙壁撞击 — 短促轻击"""
        rate = 22050
        duration = 0.04
        n = int(rate * duration)
        samples = []
        for i in range(n):
            t = i / rate
            progress = t / duration
            val = math.sin(2 * math.pi * 300 * t)
            env = (1.0 - progress) ** 3
            samples.append(val * env * 0.3)
        self._add_sound('wall_hit', samples, rate)

    def _gen_powerup(self):
        """道具拾取 — 三音上行琶音 C5→E5→G5"""
        rate = 22050
        note_duration = 0.1
        frequencies = [523, 659, 784]  # C5, E5, G5
        total_duration = note_duration * 3
        n = int(rate * total_duration)
        samples = []
        for i in range(n):
            t = i / rate
            note_idx = min(int(t / note_duration), 2)
            note_t = t - note_idx * note_duration
            freq = frequencies[note_idx]
            val = self._square_wave(freq, note_t, harmonics=2)
            # 每个音符独立的衰减
            note_progress = note_t / note_duration
            env = max(0, 1.0 - note_progress * 0.5)
            samples.append(val * env * 0.35)
        self._add_sound('powerup', samples, rate)

    def _gen_game_start(self):
        """开场音效 — 短号角曲"""
        rate = 22050
        # 音符：C4 E4 G4 C5 (每个 0.12s) + 长 C5 (0.3s)
        notes = [
            (262, 0.12), (330, 0.12), (392, 0.12),  # C E G
            (523, 0.12), (392, 0.08), (523, 0.30),   # C G C (hold)
        ]
        total = sum(d[1] for d in notes)
        n = int(rate * total)
        samples = []
        cursor = 0.0
        for freq, dur in notes:
            ns = int(rate * dur)
            for j in range(ns):
                t = j / rate
                progress = j / ns
                val = self._square_wave(freq, t, harmonics=3)
                env = max(0, 1.0 - progress * 0.7)
                samples.append(val * env * 0.4)
            cursor += dur
        self._add_sound('game_start', samples, rate)

    def _gen_game_over(self):
        """游戏结束 — 下行旋律"""
        rate = 22050
        notes = [
            (440, 0.2), (370, 0.2), (330, 0.2),  # A4 F#4 E4
            (262, 0.4),                              # C4 (长)
        ]
        total = sum(d[1] for d in notes)
        n = int(rate * total)
        samples = []
        cursor = 0.0
        for freq, dur in notes:
            ns = int(rate * dur)
            for j in range(ns):
                t = j / rate
                progress = j / ns
                val = self._square_wave(freq, t, harmonics=2)
                env = max(0, 1.0 - progress * 0.3)
                samples.append(val * env * 0.4)
            cursor += dur
        self._add_sound('game_over', samples, rate)

    def _gen_victory(self):
        """胜利音效 — 上行号角"""
        rate = 22050
        notes = [
            (392, 0.1), (523, 0.1), (659, 0.1),   # G4 C5 E5
            (784, 0.1), (1047, 0.4),                 # G5 C6 (hold)
        ]
        total = sum(d[1] for d in notes)
        n = int(rate * total)
        samples = []
        cursor = 0.0
        for freq, dur in notes:
            ns = int(rate * dur)
            for j in range(ns):
                t = j / rate
                progress = j / ns
                val = self._square_wave(freq, t, harmonics=3)
                env = max(0, 1.0 - progress * 0.4)
                samples.append(val * env * 0.4)
            cursor += dur
        self._add_sound('victory', samples, rate)

    def _gen_base_destroyed(self):
        """老窝被毁 — 重低音 + 噪声冲击"""
        rate = 22050
        duration = 0.6
        n = int(rate * duration)
        samples = []
        for i in range(n):
            t = i / rate
            progress = t / duration
            # 从 120Hz 急降到 30Hz
            freq = 120 - 90 * progress
            sine = math.sin(2 * math.pi * freq * t) * 0.5
            noise = self._noise_sample() * 0.5
            val = sine + noise
            # 先保持后衰减
            if progress < 0.3:
                env = 1.0
            else:
                env = math.exp(-(progress - 0.3) * 5)
            samples.append(val * env * 0.5)
        self._add_sound('base_destroyed', samples, rate)

    def _gen_bgm(self):
        """背景音乐 — 简单循环进行曲"""
        rate = 22050
        bpm = 140
        beat_dur = 60 / bpm   # 一拍时长 ~0.43s
        bar_beats = 4         # 4/4 拍
        bars = 4              # 4 小节循环

        total_duration = beat_dur * bar_beats * bars
        n = int(rate * total_duration)
        samples = []

        # 旋律音符 (频率, 开始拍, 持续拍)
        melody = [
            # 第1小节
            (330, 0, 0.5), (392, 0.5, 0.5), (330, 1, 0.5), (392, 1.5, 0.5),
            (440, 2, 0.5), (392, 2.5, 0.5), (330, 3, 0.5), (294, 3.5, 0.5),
            # 第2小节
            (262, 4, 0.5), (330, 4.5, 0.5), (392, 5, 0.5), (440, 5.5, 0.5),
            (392, 6, 1.0), (330, 7, 0.5), (294, 7.5, 0.5),
            # 第3小节
            (330, 8, 0.5), (392, 8.5, 0.5), (440, 9, 0.5), (523, 9.5, 0.5),
            (440, 10, 0.5), (392, 10.5, 0.5), (330, 11, 0.5), (294, 11.5, 0.5),
            # 第4小节
            (262, 12, 0.5), (294, 12.5, 0.5), (330, 13, 0.5), (262, 13.5, 0.5),
            (294, 14, 1.5), (262, 15.5, 0.5),
        ]

        # 低音线 (频率, 开始拍, 持续拍)
        bass = [
            (131, 0, 1), (165, 1, 1), (131, 2, 1), (165, 3, 1),
            (131, 4, 1), (165, 5, 1), (131, 6, 1), (165, 7, 1),
            (131, 8, 1), (165, 9, 1), (131, 10, 1), (165, 11, 1),
            (131, 12, 1), (165, 13, 1), (131, 14, 2),
        ]

        for i in range(n):
            t = i / rate
            val = 0.0

            # 合成旋律
            for freq, start, dur in melody:
                local_t = t - start * beat_dur
                if 0 <= local_t < dur * beat_dur:
                    progress = local_t / (dur * beat_dur)
                    note_val = self._square_wave(freq, local_t, harmonics=2)
                    env = max(0, 1.0 - progress * 0.6)
                    val += note_val * env * 0.18

            # 合成低音
            for freq, start, dur in bass:
                local_t = t - start * beat_dur
                if 0 <= local_t < dur * beat_dur:
                    progress = local_t / (dur * beat_dur)
                    bass_val = self._square_wave(freq, local_t, harmonics=2)
                    env = max(0, 1.0 - progress * 0.3)
                    val += bass_val * env * 0.12

            samples.append(val)

        self._add_sound('bgm', samples, rate)

    # ========== 主生成方法 ==========

    def _generate_all(self):
        """生成全部音效"""
        self._gen_shoot()
        self._gen_enemy_shoot()
        self._gen_explosion()
        self._gen_wall_hit()
        self._gen_powerup()
        self._gen_game_start()
        self._gen_game_over()
        self._gen_victory()
        self._gen_base_destroyed()
        self._gen_bgm()

    # ========== 播放接口 ==========

    def play(self, name):
        """播放指定音效"""
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def play_bgm(self, volume=0.4):
        """开始循环播放背景音乐"""
        if not self.enabled or self._bgm_playing:
            return
        bgm = self.sounds.get('bgm')
        if bgm:
            bgm.set_volume(volume)
            bgm.play(loops=-1)
            self._bgm_playing = True

    def stop_bgm(self):
        """停止背景音乐"""
        bgm = self.sounds.get('bgm')
        if bgm:
            bgm.stop()
        self._bgm_playing = False

    def set_enabled(self, enabled):
        """开关音效"""
        self.enabled = enabled
        if not enabled:
            self.stop_bgm()
