import math
import random
import pygame
from constants import *

class Particle:
    def __init__(self, x, y, dx, dy, color, size, lifetime, decay=0.96):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        self.max_life = lifetime
        self.life = lifetime
        self.decay = decay

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dx *= self.decay
        self.dy *= self.decay
        self.life -= 1

    def draw(self, surface):
        pct = max(0.01, self.life / self.max_life)
        size = max(1, int(self.size * pct))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

class ParticleEngine:
    def __init__(self):
        self.particles = []

    def spawn_explosion(self, x, y, palette, count=30, size_range=(2, 6)):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 7.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            color = random.choice(palette)
            size = random.randint(size_range[0], size_range[1])
            life = random.randint(15, 50)
            self.particles.append(Particle(x, y, dx, dy, color, size, life))

    def spawn_spark(self, x, y, dx, dy, color):
        self.particles.append(Particle(x, y, dx, dy, color, random.randint(1, 3), random.randint(8, 20), 0.98))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class FloatingText:
    def __init__(self, x, y, text, color, size=18):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.dy = -1.2
        self.life = 60
        self.max_life = 60
        self.font = pygame.font.SysFont("Courier New", size, bold=True)

    def update(self):
        self.y += self.dy
        self.life -= 1

    def draw(self, surface):
        alpha = int((self.life / self.max_life) * 255)
        txt_surf = self.font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surface.blit(txt_surf, (self.x - txt_surf.get_width() // 2, self.y))

class TextManager:
    def __init__(self):
        self.texts = []

    def spawn(self, x, y, text, color, size=18):
        self.texts.append(FloatingText(x, y, text, color, size))

    def update(self):
        for t in self.texts[:]:
            t.update()
            if t.life <= 0:
                self.texts.remove(t)

    def draw(self, surface):
        for t in self.texts:
            t.draw(surface)

class CameraShake:
    def __init__(self):
        self.amplitude = 0
        self.duration = 0

    def trigger(self, amplitude, duration):
        self.amplitude = amplitude
        self.duration = duration

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            if self.duration == 0:
                self.amplitude = 0

    def get_offset(self):
        if self.duration > 0:
            return random.randint(-self.amplitude, self.amplitude), random.randint(-self.amplitude, self.amplitude)
        return 0, 0

effects = ParticleEngine()
floating_text = TextManager()
camera_shake = CameraShake()