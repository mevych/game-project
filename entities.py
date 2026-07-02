import math
import random
import pygame
from constants import *
from sound import sfx
from effects import effects, floating_text, camera_shake

def get_bezier_point(p0, p1, p2, p3, t):
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return x, y

class Starfield:
    def __init__(self, lvl=1):
        self.stars = []
        self.regenerate_stars(lvl)

    def regenerate_stars(self, lvl=1):
        self.stars.clear()
        if lvl == 1:
            palette = [(45, 50, 65), (55, 60, 75), (70, 75, 90)]
        elif lvl == 2:
            palette = [(65, 35, 55), (75, 45, 65), (90, 50, 80)]
        else:
            palette = [(65, 50, 35), (75, 60, 45), (90, 70, 50)]

        for _ in range(45):
            self.stars.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'speed': random.uniform(0.3, 1.3),
                'color': random.choice(palette),
                'size': random.uniform(0.8, 1.8)
            })

    def update(self, speed_multiplier=1.0):
        for star in self.stars:
            star['y'] += star['speed'] * speed_multiplier
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface):
        for star in self.stars:
            pygame.draw.circle(surface, star['color'], (int(star['x']), int(star['y'])), int(star['size']))

class Laser:
    def __init__(self, x, y, dx, dy, color, damage=1, size=(4, 15)):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.damage = damage
        self.width, self.height = size

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface):
        rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect, border_radius=2)
        pygame.draw.line(surface, COLOR_WHITE, (self.x, self.y - self.height // 3), (self.x, self.y + self.height // 3), 2)

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class WingmanDrone:
    def __init__(self, offset_x):
        self.offset_x = offset_x
        self.x = 0
        self.y = 0
        self.angle_offset = 0.0
        self.shoot_cooldown = 0
        self.max_cooldown = 28

    def update(self, player_x, player_y, lasers):
        self.angle_offset += 0.06
        self.x = player_x + self.offset_x + math.sin(self.angle_offset) * 8
        self.y = player_y + 15 + math.cos(self.angle_offset) * 6

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            self.shoot_cooldown = self.max_cooldown
            sfx.play('wingman_shoot')
            lasers.append(Laser(self.x, self.y - 10, 0, -8, COLOR_CYAN, damage=1, size=(3, 10)))

        if random.random() < 0.2:
            effects.spawn_spark(self.x, self.y + 5, random.uniform(-0.5, 0.5), random.uniform(1, 2), COLOR_BLUE)

    def draw(self, surface):
        points = [
            (self.x, self.y - 8),
            (self.x - 7, self.y + 5),
            (self.x, self.y + 2),
            (self.x + 7, self.y + 5)
        ]
        pygame.draw.polygon(surface, COLOR_BLUE, points)
        pygame.draw.polygon(surface, COLOR_WHITE, points, 1)
        pygame.draw.circle(surface, COLOR_CYAN, (int(self.x), int(self.y - 1)), 2)

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 90
        self.width = 45
        self.height = 40
        self.max_hp = 3
        self.hp = 3
        self.max_shield = 100
        self.shield = 40
        self.shield_regen_timer = 0
        self.speed = 5.0
        self.fire_rate_modifier = 0
        self.shoot_cooldown = 0
        self.base_weapon_level = 1
        self.weapon_level = 1
        self.invulnerable_timer = 0
        self.score = 0
        self.scrap_collected = 10000
        self.tilt = 0.0
        self.double_damage_timer = 0
        self.time_slow_timer = 0
        self.magnet_timer = 0
        self.weapon_upgrade_timer = 0
        self.drones = []

        self.sprite = None
        self.sprite_original = None
        self.load_sprite()

    def load_sprite(self):
        self.sprite_original = pygame.image.load("sprites/player.png").convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite_original, (self.width, self.height))
        self.sprite_rect = self.sprite.get_rect()

    def move(self, keys):
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed

        self.x += dx
        self.y += dy

        target_tilt = dx * 1.8
        self.tilt += (target_tilt - self.tilt) * 0.12

        if self.x < self.width // 2:
            self.x = self.width // 2
        if self.x > SCREEN_WIDTH - self.width // 2:
            self.x = SCREEN_WIDTH - self.width // 2
        if self.y < SCREEN_HEIGHT // 2:
            self.y = SCREEN_HEIGHT // 2
        if self.y > SCREEN_HEIGHT - 60:
            self.y = SCREEN_HEIGHT - 60

    def add_wingman(self):
        if len(self.drones) == 0:
            self.drones.append(WingmanDrone(-40))
        elif len(self.drones) == 1:
            self.drones.append(WingmanDrone(40))

    def shoot(self, lasers):
        if self.shoot_cooldown == 0:
            sfx.play('shoot')
            base_cooldown = 15
            cooldown_reduction = min(8, self.fire_rate_modifier * 1.5)
            self.shoot_cooldown = max(6, int(base_cooldown - cooldown_reduction))

            color = COLOR_MAGENTA if self.double_damage_timer > 0 else COLOR_CYAN
            dmg = 2 if self.double_damage_timer > 0 else 1

            if self.weapon_level == 1:
                lasers.append(Laser(self.x, self.y - 15, 0, -11, color, damage=dmg))
            elif self.weapon_level == 2:
                lasers.append(Laser(self.x - 14, self.y - 10, 0, -12, color, damage=dmg))
                lasers.append(Laser(self.x + 14, self.y - 10, 0, -12, color, damage=dmg))
            elif self.weapon_level >= 3:
                lasers.append(Laser(self.x, self.y - 18, 0, -13, color, damage=dmg))
                lasers.append(Laser(self.x - 18, self.y - 5, -1.8, -12, color, damage=dmg))
                lasers.append(Laser(self.x + 18, self.y - 5, 1.8, -12, color, damage=dmg))

    def damage(self, amt=1):
        if self.invulnerable_timer > 0:
            return False

        if self.shield > 0:
            self.shield -= 35
            if self.shield < 0:
                self.shield = 0
            self.invulnerable_timer = 30
            camera_shake.trigger(8, 12)
            sfx.play('hurt')
            floating_text.spawn(self.x, self.y - 20, "SHIELD ABSORBED", COLOR_BLUE, 15)
            return False
        else:
            self.hp -= amt
            self.invulnerable_timer = 60
            camera_shake.trigger(16, 25)
            sfx.play('hurt')
            effects.spawn_explosion(self.x, self.y, [COLOR_RED, COLOR_ORANGE, COLOR_WHITE], 40)
            floating_text.spawn(self.x, self.y - 20, "SYSTEM DAMAGE!", COLOR_RED, 18)
            if self.hp <= 0:
                return True
        return False

    def update(self, lasers):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.double_damage_timer > 0:
            self.double_damage_timer -= 1
        if self.time_slow_timer > 0:
            self.time_slow_timer -= 1
        if self.magnet_timer > 0:
            self.magnet_timer -= 1

        if self.weapon_level > self.base_weapon_level:
            if self.weapon_upgrade_timer > 0:
                self.weapon_upgrade_timer -= 1
            else:
                self.weapon_level -= 1
                if self.weapon_level > self.base_weapon_level:
                    self.weapon_upgrade_timer = 450
                floating_text.spawn(self.x, self.y - 20, "WEAPONS DEGRADED", COLOR_RED, 14)

        self.shield_regen_timer += 1
        if self.shield_regen_timer >= 90:
            self.shield_regen_timer = 0
            if self.shield < self.max_shield:
                self.shield = min(self.max_shield, self.shield + 2)

        offset_tilt = self.tilt * 0.4
        effects.spawn_spark(self.x - offset_tilt, self.y + 16, random.uniform(-0.8, 0.8), random.uniform(3, 5), COLOR_ORANGE)
        if random.random() < 0.3:
            effects.spawn_spark(self.x - offset_tilt, self.y + 16, random.uniform(-1, 1), random.uniform(2, 4), COLOR_YELLOW)

        for drone in self.drones:
            drone.update(self.x, self.y, lasers)

    def draw(self, surface):
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 6) % 2 == 0:
            return

        if self.sprite:
            if self.tilt != 0:
                rotated_sprite = pygame.transform.rotate(self.sprite, self.tilt * 0.5)
                rect = rotated_sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(rotated_sprite, rect)
            else:
                rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(self.sprite, rect)

            if self.double_damage_timer > 0:
                glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 0, 255, 80), (self.width // 2 + 10, self.height // 2 + 10), max(self.width, self.height) // 2 + 5)
                surface.blit(glow_surf, (int(self.x - self.width // 2 - 10), int(self.y - self.height // 2 - 10)))

        if self.shield > 0:
            shield_radius = int(self.width * 0.85)
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            alpha = int(45 + math.sin(pygame.time.get_ticks() * 0.01) * 25)
            pygame.draw.circle(shield_surf, (0, 255, 150, alpha), (shield_radius, shield_radius), shield_radius, 2)
            surface.blit(shield_surf, (self.x - shield_radius, self.y - shield_radius))

        for drone in self.drones:
            drone.draw(surface)

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class Enemy:
    def __init__(self, grid_x, grid_y, target_x, target_y, type_id=1, game=None):
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.home_x = target_x
        self.home_y = target_y
        self.x = target_x
        self.y = -60
        self.type_id = type_id
        self.hp = 1
        self.max_hp = 1
        self.speed = 3.0
        self.score_value = 100
        self.width = 32
        self.height = 32
        self.shield = 0
        self.state = "entering"
        self.anim_timer = random.uniform(0, 50)
        self.bezier_t = 0.0
        self.bezier_speed = 0.015
        self.init_bezier_path()
        self.setup_attributes()

        if self.type_id == 5:
            sprite_path = "sprites/enemies/enemy5.png"
        else:
            sprite_path = f"sprites/enemies/enemy{self.type_id}.png"

        self.sprite = pygame.image.load(sprite_path).convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))

    def init_bezier_path(self):
        self.p0 = (random.choice([-100, SCREEN_WIDTH + 100]), random.uniform(0, 300))
        self.p1 = (SCREEN_WIDTH // 2, random.uniform(100, 400))
        self.p2 = (self.home_x + random.uniform(-150, 150), self.home_y + 200)
        self.p3 = (self.home_x, self.home_y)

    def setup_attributes(self):
        if self.type_id == 1:
            self.hp, self.color, self.score_value, self.speed = 1, COLOR_RED, 100, 3.0
        elif self.type_id == 2:
            self.hp, self.color, self.score_value, self.speed = 2, COLOR_YELLOW, 200, 4.0
        elif self.type_id == 3:
            self.hp, self.color, self.score_value, self.speed = 1, COLOR_PURPLE, 350, 5.2
        elif self.type_id == 4:
            self.hp, self.color, self.score_value, self.speed = 3, COLOR_ORANGE, 500, 2.5
            self.width, self.height = 38, 38
        elif self.type_id == 5:
            self.hp, self.color, self.score_value, self.speed = 4, COLOR_GREEN, 450, 3.0
            self.width, self.height = 38, 38
        elif self.type_id == 6:
            self.hp, self.color, self.score_value, self.speed = 2, COLOR_MAGENTA, 600, 3.5
        elif self.type_id == 7:
            self.hp, self.color, self.score_value, self.speed = 2, COLOR_BLUE, 750, 2.8
            self.shield = 2
        elif self.type_id == 8:
            self.hp, self.color, self.score_value, self.speed = 4, COLOR_GOLD, 900, 2.2
            self.width, self.height = 42, 42

        if self.game:
            diff = self.game.difficulty_settings[self.game.current_difficulty]
            self.hp = max(1, int(self.hp * diff["hp_mult"]))
            self.max_hp = self.hp
            self.speed = self.speed * diff["speed_mult"]

    def start_dive(self, player_x):
        self.state = "diving"
        self.dive_angle = math.atan2(SCREEN_HEIGHT - self.y, player_x - self.x)

    def update(self, player_x, enemy_lasers, time_scale=1.0):
        self.anim_timer += 0.08 * time_scale
        if self.game:
            self.game.unlock_entity(str(self.type_id))

        if self.state == "entering":
            self.bezier_t += self.bezier_speed * time_scale
            if self.bezier_t >= 1.0:
                self.x = self.home_x
                self.y = self.home_y
                self.state = "grid"
            else:
                self.x, self.y = get_bezier_point(self.p0, self.p1, self.p2, self.p3, self.bezier_t)

        elif self.state == "grid":
            sway_x = math.sin(pygame.time.get_ticks() * 0.0022) * 16
            sway_y = math.cos(pygame.time.get_ticks() * 0.0011 + self.grid_x) * 6
            self.x = self.home_x + sway_x
            self.y = self.home_y + sway_y

            if self.game:
                diff = self.game.difficulty_settings[self.game.current_difficulty]
                shoot_prob = 0.0008 * time_scale * diff["fire_mult"]
            else:
                shoot_prob = 0.0008 * time_scale

            if self.type_id in [4, 6, 8]: shoot_prob *= 3
            if random.random() < shoot_prob:
                self.fire_laser(enemy_lasers)

        elif self.state == "diving":
            if self.type_id == 3:
                t_angle = math.atan2(SCREEN_HEIGHT - self.y, player_x - self.x)
                self.dive_angle += (t_angle - self.dive_angle) * 0.04 * time_scale

            self.x += math.cos(self.dive_angle) * self.speed * time_scale
            self.y += math.sin(self.dive_angle) * self.speed * time_scale

            shoot_prob = 0.012 if self.type_id in [2, 4, 6, 8] else 0.004
            if self.game:
                diff = self.game.difficulty_settings[self.game.current_difficulty]
                shoot_prob *= diff["fire_mult"]

            if random.random() < shoot_prob * time_scale:
                self.fire_laser(enemy_lasers)

            if self.y > SCREEN_HEIGHT + 30 or self.x < -150 or self.x > SCREEN_WIDTH + 150:
                self.y = -40
                self.x = self.home_x
                self.state = "returning"

        elif self.state == "returning":
            dx = self.home_x - self.x
            dy = self.home_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 6:
                self.state = "grid"
            elif dist > 0:
                self.x += (dx / dist) * self.speed * 1.6 * time_scale
                self.y += (dy / dist) * self.speed * 1.6 * time_scale

    def fire_laser(self, lasers):
        sfx.play('enemy_shoot')
        if self.type_id == 4:
            lasers.append(Laser(self.x, self.y + 15, 0, 11, COLOR_PURPLE, damage=1, size=(5, 20)))
        elif self.type_id == 6:
            lasers.append(Laser(self.x - 8, self.y + 12, -1, 7, COLOR_MAGENTA, damage=1))
            lasers.append(Laser(self.x + 8, self.y + 12, 1, 7, COLOR_MAGENTA, damage=1))
        elif self.type_id == 8:
            lasers.append(Laser(self.x, self.y + 15, 0, 9, COLOR_GOLD, damage=2, size=(7, 22)))
        else:
            lasers.append(Laser(self.x, self.y + 12, 0, 6, self.color, damage=1))

    def draw(self, surface):
        if self.state == "grid":
            angle = math.sin(self.anim_timer) * 3
            rotated = pygame.transform.rotate(self.sprite, angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)
        else:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sprite, rect)

        if self.shield > 0:
            pygame.draw.circle(surface, COLOR_CYAN, (int(self.x), int(self.y)), 22, 1)

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class SpaceMine:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width, self.height = 20, 20
        self.speed = 1.0
        self.pulse_timer = 0
        self.hp = 1

    def update(self, time_scale=1.0):
        self.y += self.speed * time_scale
        self.pulse_timer += 0.15 * time_scale

    def draw(self, surface):
        pulse_val = abs(math.sin(self.pulse_timer))
        glow_radius = int(12 + pulse_val * 8)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 60, 60, int(80 - pulse_val * 60)), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (self.x - glow_radius, self.y - glow_radius))

        pygame.draw.circle(surface, COLOR_RED, (int(self.x), int(self.y)), 6)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 3)

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class EnemyBomber(Enemy):
    def __init__(self, grid_x, grid_y, target_x, target_y, game=None):
        super().__init__(grid_x, grid_y, target_x, target_y, type_id=5, game=game)
        self.hp = 4
        self.max_hp = 4
        self.color = COLOR_GREEN
        self.score_value = 450
        self.mine_cooldown = random.randint(100, 300)

        if self.game:
            diff = self.game.difficulty_settings[self.game.current_difficulty]
            self.hp = max(1, int(self.hp * diff["hp_mult"]))
            self.max_hp = self.hp

    def update(self, player_x, enemy_lasers, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("5")
        res = super().update(player_x, enemy_lasers, time_scale)

        if self.state == "grid":
            if self.mine_cooldown > 0:
                self.mine_cooldown -= 1 * time_scale
            else:
                self.mine_cooldown = random.randint(250, 400)
                return "spawn_mine"
        return res

    def draw(self, surface):
        super().draw(surface)

class Asteroid:
    def __init__(self):
        self.x = random.uniform(50, SCREEN_WIDTH - 50)
        self.y = -60
        self.speed = random.uniform(1.5, 3.5)
        self.size = random.randint(20, 45)
        self.hp = max(1, self.size // 10)
        self.rotation_angle = 0.0
        self.rotation_speed = random.uniform(-0.04, 0.04)

        rock_number = random.randint(1, 5)
        sprite_path = f"sprites/rock{rock_number}.png"
        self.sprite = pygame.image.load(sprite_path).convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (self.size * 2, self.size * 2))

    def update(self, time_scale=1.0):
        self.y += self.speed * time_scale
        self.rotation_angle += self.rotation_speed * time_scale

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.sprite, math.degrees(self.rotation_angle))
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

class PowerUp:
    def __init__(self, x, y, type_id=None):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.speed = 2.0
        self.life = 600

        if type_id is None:
            self.type_id = random.choices([1, 2, 4, 5, 6, 7], weights=[15, 15, 40, 10, 10, 10])[0]
        else:
            self.type_id = type_id

        self.setup_visuals()

    def setup_visuals(self):
        mapping = {
            1: ('W', COLOR_CYAN),
            2: ('S', COLOR_GREEN),
            4: ('$', COLOR_GOLD),
            5: ('D', COLOR_MAGENTA),
            6: ('T', COLOR_BLUE),
            7: ('M', COLOR_ORANGE)
        }
        self.char, self.color = mapping.get(self.type_id, ('?', COLOR_WHITE))
        self.font = pygame.font.SysFont("Courier New", 16, bold=True)

    def update(self):
        self.y += self.speed
        self.life -= 1

    def draw(self, surface):
        rect = self.get_rect()
        pygame.draw.rect(surface, COLOR_DARK_GREY, rect, border_radius=4)
        pygame.draw.rect(surface, self.color, rect, 2, border_radius=4)
        char_surf = self.font.render(self.char, True, self.color)
        surface.blit(char_surf, (self.x - char_surf.get_width() // 2, self.y - char_surf.get_height() // 2))

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class ShieldOrb:
    def __init__(self, angle_offset, radius, parent):
        self.angle_offset = angle_offset
        self.radius = radius
        self.parent = parent
        self.x = 0
        self.y = 0
        self.hp = 8

    def update(self, angle_speed, time_scale=1.0):
        self.angle_offset += angle_speed * time_scale
        self.x = self.parent.x + math.cos(self.angle_offset) * self.radius
        self.y = self.parent.y + math.sin(self.angle_offset) * self.radius

    def draw(self, surface):
        pygame.draw.circle(surface, COLOR_CYAN, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 6)

class BaseBoss:
    def __init__(self, name, hp, color, game=None, sprite_path=None):
        self.game = game
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.color = color
        self.x = SCREEN_WIDTH // 2
        self.y = -100
        self.target_y = 150
        self.width = 110
        self.height = 90
        self.speed = 1.5
        self.shoot_cooldown = 0
        self.movement_timer = 0
        self.state = "entering"

        self.sprite = None
        self.sprite_path = sprite_path
        self.load_sprite()

    def load_sprite(self):
        if self.sprite_path:
            try:
                original = pygame.image.load(self.sprite_path).convert_alpha()
                self.sprite = pygame.transform.scale(original, (self.width, self.height))
            except Exception as e:
                print(f"Could not load boss sprite {self.sprite_path}: {e}")
                self.sprite = None

    def draw(self, surface):
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sprite, rect)
        else:
            self.draw_primitives(surface)

        self.draw_health_bar(surface)

    def draw_primitives(self, surface):
        pass

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def draw_health_bar(self, surface):
        font = pygame.font.SysFont("Courier New", 16, bold=True)
        text = font.render(f"{self.name}: {self.hp}/{self.max_hp} HP", True, COLOR_RED)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 10))

        bar_width = 400
        bar_height = 14
        bx = SCREEN_WIDTH // 2 - bar_width // 2
        by = 32
        pygame.draw.rect(surface, COLOR_DARK_GREY, (bx, by, bar_width, bar_height), border_radius=3)
        if self.hp > 0:
            pct = self.hp / self.max_hp
            pygame.draw.rect(surface, COLOR_RED, (bx, by, int(bar_width * pct), bar_height), border_radius=3)

class BossSentinel(BaseBoss):
    def __init__(self, game=None):
        super().__init__("SENTINEL-X", 50, COLOR_ORANGE, game=game, sprite_path="sprites/bosses/sentinel.png")
        self.width = 90
        self.height = 70
        self.load_sprite()

    def draw_primitives(self, surface):
        pts = [
            (self.x, self.y + 35),
            (self.x - 45, self.y),
            (self.x - 25, self.y - 35),
            (self.x, self.y - 15),
            (self.x + 25, self.y - 35),
            (self.x + 45, self.y)
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
        eye_pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
        eye_color = (255, int(50 + eye_pulse * 150), 50)
        pygame.draw.circle(surface, eye_color, (int(self.x), int(self.y + 5)), 8)

    def update(self, player_x, enemy_lasers, enemies, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("SENTINEL-X")
        if self.state == "entering":
            self.y += 2.0 * time_scale
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "active"
        else:
            self.movement_timer += 0.02 * time_scale
            self.x = SCREEN_WIDTH // 2 + math.sin(self.movement_timer) * 220

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1 * time_scale
            else:
                self.shoot_cooldown = random.randint(40, 70)
                sfx.play('boss_shoot')
                enemy_lasers.append(Laser(self.x - 30, self.y + 20, 0, 7, COLOR_RED, damage=1, size=(5, 18)))
                enemy_lasers.append(Laser(self.x + 30, self.y + 20, 0, 7, COLOR_RED, damage=1, size=(5, 18)))
                if random.random() < 0.4:
                    angle = math.atan2(SCREEN_HEIGHT - self.y, player_x - self.x)
                    dx = math.cos(angle) * 8
                    dy = math.sin(angle) * 8
                    enemy_lasers.append(Laser(self.x, self.y + 25, dx, dy, COLOR_ORANGE, damage=1, size=(5, 15)))

class BossVoidReaver(BaseBoss):
    def __init__(self, game=None):
        super().__init__("VOID REAVER", 90, COLOR_PURPLE, game=game, sprite_path="sprites/bosses/void_reaver.png")
        self.width = 110
        self.height = 80
        self.load_sprite()
        self.shield_active = True
        self.orbs = [
            ShieldOrb(0, 70, self),
            ShieldOrb(math.pi * 2 / 3, 70, self),
            ShieldOrb(math.pi * 4 / 3, 70, self)
        ]
        self.orb_angle_speed = 0.04

    def draw_primitives(self, surface):
        pts = [
            (self.x, self.y - 40),
            (self.x - 55, self.y - 10),
            (self.x - 20, self.y + 40),
            (self.x, self.y + 15),
            (self.x + 20, self.y + 40),
            (self.x + 55, self.y - 10)
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
        if self.shield_active:
            for orb in self.orbs:
                orb.draw(surface)
            shield_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 200, 255, 30), (90, 90), 85, 2)
            surface.blit(shield_surf, (self.x - 90, self.y - 90))

    def update(self, player_x, enemy_lasers, enemies, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("VOID REAVER")
        if self.state == "entering":
            self.y += 1.5 * time_scale
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "active"
        else:
            self.movement_timer += 0.012 * time_scale
            self.x = SCREEN_WIDTH // 2 + math.sin(self.movement_timer) * 180
            self.y = self.target_y + math.cos(self.movement_timer * 1.5) * 40

            if self.shield_active:
                active_orbs = []
                for orb in self.orbs:
                    orb.update(self.orb_angle_speed, time_scale)
                    if orb.hp > 0:
                        active_orbs.append(orb)
                self.orbs = active_orbs
                if len(self.orbs) == 0:
                    self.shield_active = False
                    floating_text.spawn(self.x, self.y - 50, "VOID SHIELD DEACTIVATED", COLOR_RED, 20)

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1 * time_scale
            else:
                self.shoot_cooldown = random.randint(50, 80)
                sfx.play('boss_shoot')
                enemy_lasers.append(Laser(self.x, self.y + 30, 0, 6, COLOR_PURPLE, damage=1, size=(6, 20)))
                enemy_lasers.append(Laser(self.x - 20, self.y + 25, -1.5, 6, COLOR_PURPLE, damage=1, size=(5, 18)))
                enemy_lasers.append(Laser(self.x + 20, self.y + 25, 1.5, 6, COLOR_PURPLE, damage=1, size=(5, 18)))

                if self.shield_active and len(enemies) < 4 and random.random() < 0.5:
                    spawn_x = self.x + random.choice([-80, 80])
                    new_enemy = Enemy(0, 0, spawn_x, self.y + 40, type_id=1, game=self.game)
                    new_enemy.state = "diving"
                    new_enemy.dive_angle = math.pi / 2
                    enemies.append(new_enemy)

    def draw(self, surface):
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sprite, rect)
        else:
            self.draw_primitives(surface)

        if self.shield_active:
            for orb in self.orbs:
                pygame.draw.circle(surface, (255, 0, 0), (int(orb.x), int(orb.y)), 14)
                pygame.draw.circle(surface, (255, 100, 100), (int(orb.x), int(orb.y)), 8)
                pygame.draw.circle(surface, (255, 255, 255), (int(orb.x - 3), int(orb.y - 3)), 3)

            shield_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (255, 0, 0, 40), (90, 90), 85, 2)
            surface.blit(shield_surf, (self.x - 90, self.y - 90))

        self.draw_health_bar(surface)

class BossLeviathan(BaseBoss):
    def __init__(self, game=None):
        super().__init__("LEVIATHAN ETERNAL", 160, COLOR_RED, game=game, sprite_path="sprites/bosses/leviathan.png")
        self.width = 150
        self.height = 100
        self.load_sprite()
        self.target_y = 130

    def draw_primitives(self, surface):
        pts = [
            (self.x, self.y - 50),
            (self.x - 75, self.y - 30),
            (self.x - 55, self.y + 15),
            (self.x - 15, self.y + 45),
            (self.x, self.y + 20),
            (self.x + 15, self.y + 45),
            (self.x + 55, self.y + 15),
            (self.x + 75, self.y - 30)
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
        core_pulse = abs(math.sin(pygame.time.get_ticks() * 0.01))
        core_color = (255, int(150 + core_pulse * 105), 0)
        pygame.draw.rect(surface, core_color, (self.x - 20, self.y - 15, 40, 20), border_radius=4)
        pygame.draw.rect(surface, COLOR_WHITE, (self.x - 10, self.y - 10, 20, 10), border_radius=2)

    def update(self, player_x, enemy_lasers, enemies, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("LEVIATHAN ETERNAL")
        if self.state == "entering":
            self.y += 1.0 * time_scale
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "active"
        else:
            self.movement_timer += 0.008 * time_scale
            self.x = SCREEN_WIDTH // 2 + math.sin(self.movement_timer) * 120
            self.y = self.target_y + math.cos(self.movement_timer * 2) * 20

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1 * time_scale
            else:
                self.shoot_cooldown = random.randint(35, 60)
                sfx.play('boss_shoot')
                num_lasers = 5 if self.hp > self.max_hp // 2 else 8
                base_angle = math.pi / 2
                spread = math.pi / 4
                for i in range(num_lasers):
                    if num_lasers > 1:
                        angle = base_angle - spread + (i / (num_lasers - 1)) * (spread * 2)
                    else:
                        angle = base_angle
                    dx = math.cos(angle) * 6
                    dy = math.sin(angle) * 6
                    enemy_lasers.append(Laser(self.x, self.y + 40, dx, dy, COLOR_RED, damage=1, size=(6, 16)))

                if self.hp < self.max_hp // 2 and random.random() < 0.3:
                    enemy_lasers.append(Laser(self.x, self.y + 40, 0, 9, COLOR_GOLD, damage=2, size=(10, 30)))

class BossOverlord(BaseBoss):
    def __init__(self, game=None):
        super().__init__("OVERLORD DREADNOUGHT", 220, COLOR_MAGENTA, game=game, sprite_path="sprites/bosses/overlord.png")
        self.width = 160
        self.height = 100
        self.load_sprite()
        self.target_y = 140

    def draw_primitives(self, surface):
        pts = [
            (self.x, self.y - 45),
            (self.x - 80, self.y - 15),
            (self.x - 60, self.y + 35),
            (self.x - 30, self.y + 15),
            (self.x, self.y + 45),
            (self.x + 30, self.y + 15),
            (self.x + 60, self.y + 35),
            (self.x + 80, self.y - 15)
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
        pygame.draw.line(surface, COLOR_CYAN, (self.x - 80, self.y - 15), (self.x - 100, self.y + 10), 3)
        pygame.draw.line(surface, COLOR_CYAN, (self.x + 80, self.y - 15), (self.x + 100, self.y + 10), 3)

    def update(self, player_x, enemy_lasers, enemies, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("OVERLORD")
        if self.state == "entering":
            self.y += 1.2 * time_scale
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "active"
        else:
            self.movement_timer += 0.01 * time_scale
            self.x = SCREEN_WIDTH // 2 + math.sin(self.movement_timer) * 140
            self.y = self.target_y + math.cos(self.movement_timer * 1.5) * 15

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1 * time_scale
            else:
                self.shoot_cooldown = random.randint(30, 50)
                sfx.play('boss_shoot')
                enemy_lasers.append(Laser(self.x, self.y + 45, 0, 8, COLOR_MAGENTA, damage=1, size=(6, 22)))
                enemy_lasers.append(Laser(self.x - 40, self.y + 35, -1, 7, COLOR_RED, damage=1, size=(5, 18)))
                enemy_lasers.append(Laser(self.x + 40, self.y + 35, 1, 7, COLOR_RED, damage=1, size=(5, 18)))

                if random.random() < 0.3:
                    for dx in [-3, -1.5, 0, 1.5, 3]:
                        enemy_lasers.append(Laser(self.x, self.y + 40, dx, 9, COLOR_ORANGE, damage=1, size=(4, 20)))

            if random.random() < 0.02 * time_scale:
                effects.spawn_spark(self.x, self.y + 20, random.uniform(-2, 2), random.uniform(2, 4), COLOR_MAGENTA)

class BossAetherius(BaseBoss):
    def __init__(self, game=None):
        super().__init__("BIG BOSS", 300, COLOR_CYAN, game=game, sprite_path="sprites/bosses/aetherius.png")
        self.width = 170
        self.height = 110
        self.load_sprite()
        self.target_y = 120

    def draw_primitives(self, surface):
        pts = [
            (self.x, self.y - 55),
            (self.x - 55, self.y - 35),
            (self.x - 85, self.y + 10),
            (self.x - 40, self.y + 45),
            (self.x, self.y + 55),
            (self.x + 40, self.y + 45),
            (self.x + 85, self.y + 10),
            (self.x + 55, self.y - 35)
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
        core_size = int(25 + math.sin(pygame.time.get_ticks() * 0.01) * 8)
        pygame.draw.circle(surface, COLOR_MAGENTA, (int(self.x), int(self.y)), core_size, 2)
        pygame.draw.circle(surface, COLOR_GOLD, (int(self.x), int(self.y)), 10)

    def update(self, player_x, enemy_lasers, enemies, time_scale=1.0):
        if self.game:
            self.game.unlock_entity("BIG BOSS")
        if self.state == "entering":
            self.y += 1.0 * time_scale
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "active"
        else:
            self.movement_timer += 0.007 * time_scale
            self.x = SCREEN_WIDTH // 2 + math.sin(self.movement_timer) * 160
            self.y = self.target_y + math.sin(self.movement_timer * 2.2) * 25

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1 * time_scale
            else:
                self.shoot_cooldown = random.randint(25, 45)
                sfx.play('boss_shoot')
                angle_step = math.pi / 6
                for i in range(12):
                    angle = i * angle_step + (self.movement_timer * 5)
                    dx = math.cos(angle) * 5
                    dy = math.sin(angle) * 5
                    enemy_lasers.append(Laser(self.x, self.y + 20, dx, dy, COLOR_CYAN, damage=1, size=(5, 12)))

                enemy_lasers.append(Laser(self.x, self.y + 50, 0, 10, COLOR_GOLD, damage=2, size=(8, 30)))
                target_angle = math.atan2(SCREEN_HEIGHT - self.y, player_x - self.x)
                fdx = math.cos(target_angle) * 7
                fdy = math.sin(target_angle) * 7
                enemy_lasers.append(Laser(self.x, self.y + 30, fdx, fdy, COLOR_YELLOW, damage=1, size=(6, 16)))

            if random.random() < 0.04 * time_scale:
                effects.spawn_spark(self.x, self.y, random.uniform(-4, 4), random.uniform(-4, 4), COLOR_CYAN)