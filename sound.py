import math
import random
import struct
import pygame
import os

if not pygame.mixer.get_init():
    pygame.mixer.pre_init(22050, -16, 2, 512)
    pygame.mixer.init()

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.music_enabled = True
        self.sounds = {}
        self.sound_dir = "sounds"

        if not os.path.exists(self.sound_dir):
            try:
                os.makedirs(self.sound_dir)
            except Exception as e:
                print(f"Не удалось создать директорию {self.sound_dir}: {e}")

        try:
            self.load_or_generate_sfx()
        except Exception as e:
            print(f"Аудиосистема отключена или инициализирована с ошибкой: {e}")
            self.enabled = False

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()

    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.stop()

    def play_music(self, file_path, volume=0.3):
        if not self.enabled or not self.music_enabled:
            return

        self.stop_music()

        if os.path.exists(file_path):
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1, fade_ms=500)
            except Exception as e:
                print(f"Не удалось воспроизвести музыкальный файл {file_path}: {e}")
        else:
            print(f"Файл фоновой музыки не найден по пути: {file_path}")

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def load_or_generate_sfx(self):
        sfx_files = {
            'shoot': 'shoot.wav',
            'wingman_shoot': 'wingman_shoot.wav',
            'explosion': 'explosion.wav',
            'death': 'death.mp3',
            'hurt': 'hurt.wav',
            'powerup': 'powerup.wav',
            'enemy_shoot': 'enemy_shoot.wav',
            'boss_shoot': 'boss_shoot.wav',
            'click': 'click.wav',
            'slot_tick': 'slot_tick.wav',
            'slot_win': 'slot_win.wav',
            'slot_lose': 'slot_lose.wav'
        }

        for sfx_name, file_name in sfx_files.items():
            full_path = os.path.join(self.sound_dir, file_name)
            if os.path.exists(full_path):
                try:
                    self.sounds[sfx_name] = pygame.mixer.Sound(full_path)
                except Exception as e:
                    print(f"Ошибка загрузки файла {full_path}: {e}. Переход на резервную генерацию.")
                    self.generate_fallback_sfx(sfx_name)
            else:
                self.generate_fallback_sfx(sfx_name)

    def _create_sound_from_buffer(self, buffer_data):
        return pygame.mixer.Sound(buffer=bytes(buffer_data))

    def generate_fallback_sfx(self, name):
        sample_rate = 22050
        buf = bytearray()

        if name == 'shoot':
            dur = 0.15
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 1100 - (t / dur) * 700
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 12000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'wingman_shoot':
            dur = 0.1
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 900 - (t / dur) * 500
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 8000)
                buf.extend(struct.pack('<h', val_int))

        elif name in ['explosion', 'death']:
            dur = 0.45
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                envelope = (num_samples - i) / num_samples
                val = random.uniform(-1.0, 1.0)
                val_int = int(val * envelope * 14000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'hurt':
            dur = 0.3
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 280 - (t / dur) * 180
                val = math.sin(2 * math.pi * freq * t) if (i // 80) % 2 == 0 else 0
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 15000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'powerup':
            dur = 0.4
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                phase = int(t * 15)
                notes = [523, 659, 784, 1046]
                freq = notes[phase % len(notes)]
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 10000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'enemy_shoot':
            dur = 0.2
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 400 + (t / dur) * 200
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 5000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'boss_shoot':
            dur = 0.35
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 150 + math.sin(t * 80) * 40
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 9000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'click':
            dur = 0.1
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 700 + (t / dur) * 300
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 9000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'slot_tick':
            dur = 0.08
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 150 + (t / dur) * 100
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 12000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'slot_win':
            dur = 0.6
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                phase = int(t * 18)
                notes = [523, 659, 784, 1046, 784, 1046, 1318]
                freq = notes[phase % len(notes)]
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 14000)
                buf.extend(struct.pack('<h', val_int))

        elif name == 'slot_lose':
            dur = 0.5
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                freq = 300 - (t / dur) * 200
                val = math.sin(2 * math.pi * freq * t)
                envelope = (num_samples - i) / num_samples
                val_int = int(val * envelope * 14000)
                buf.extend(struct.pack('<h', val_int))

        if len(buf) > 0:
            self.sounds[name] = self._create_sound_from_buffer(buf)

sfx = SoundManager()