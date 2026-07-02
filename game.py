import math
import random
import json
import os
import pygame
from constants import *
from sound import sfx
from effects import effects, floating_text, camera_shake
from leaderboard import Leaderboard
from entities import (
    Starfield, Laser, Player, Enemy, SpaceMine, EnemyBomber, Asteroid, PowerUp,
    BossSentinel, BossVoidReaver, BossLeviathan, BossOverlord, BossAetherius
)

class Game:
    def __init__(self):
        self.state = "MENU"
        self.starfield = Starfield(lvl=1)
        self.crt_overlay = self.create_crt_mask()

        self.player = None
        self.enemies = []
        self.enemy_lasers = []
        self.player_lasers = []
        self.powerups = []
        self.asteroids = []
        self.mines = []
        self.boss = None

        self.level = 1
        self.stage = 1
        self.max_stages = 5
        self.max_levels = 3
        self.freeplay_mode = False
        self.paused = False
        self.score_multiplier = 1.0
        self.combo_timer = 0
        self.boss_spawned = False
        self.transition_timer = 0

        self.leaderboard = Leaderboard()

        self.difficulty_settings = {
            "EASY": {"hp_mult": 0.75, "speed_mult": 0.75, "fire_mult": 0.5, "player_hp": 4},
            "NORMAL": {"hp_mult": 1.0, "speed_mult": 1.0, "fire_mult": 1.0, "player_hp": 3},
            "HARD": {"hp_mult": 1.35, "speed_mult": 1.25, "fire_mult": 1.5, "player_hp": 2}
        }
        self.current_difficulty = "NORMAL"

        self.shop_prices = {
            'hull': 15, 'shield': 15, 'speed': 20, 'fire_rate': 25, 'weapon_level': 40, 'wingman': 60
        }

        self.casino_reels = ["?", "?", "?"]
        self.casino_spin_timer = 0
        self.casino_spin_duration = 100
        self.casino_result_text = "INSERT SCRAP TO SPIN"
        self.casino_result_color = COLOR_WHITE
        self.casino_symbols = ["$", "S", "W", "C", "X"]

        self.unlocked_filename = "unlocks.json"
        self.unlocked_entries = self.load_unlocks()
        self.selected_glossary_index = 0
        self.glossary_database = {
            "1": {"name": "STANDARD INTERCEPTOR", "class": "Drone (Fighter)", "hp": "1", "threat": "Low", "desc": "The basic swarm asset. Weak titanium armor plates. Relies strictly on coordinated vector-formation attacks."},
            "2": {"name": "SWARM STINGER", "class": "Interceptor", "hp": "2", "threat": "Medium", "desc": "Agile solar-sail scout. Performs rapid horizontal maneuvers and fires targeted thermal projectiles."},
            "3": {"name": "DIVE KAMIKAZE", "class": "Kinetic Rammer", "hp": "1", "threat": "High", "desc": "Equipped with hyper-dense nose shields. Relentlessly tracks player coordinates for full-impact collision."},
            "4": {"name": "ELITE SNIPER", "class": "Tactical Artillery", "hp": "3", "threat": "Very High", "desc": "Heavy long-range support craft. Operates phase blasters capable of firing high-speed plasma bolts."},
            "5": {"name": "HEAVY BOMBER", "class": "Mine Layer", "hp": "4", "threat": "Dangerous", "desc": "Armored frame deploying passive EM mines. Denies space. Deploys defensive traps upon grid entrance."},
            "6": {"name": "STEALTH PHANTOM", "class": "Cloaked Interceptor", "hp": "2", "threat": "High", "desc": "Advanced target fitted with quantum cloaking matrices. Flickers in visibility layers and fires twin wide-angle laser spreads."},
            "7": {"name": "SHIELD CARRIER", "class": "Protector Escort", "hp": "2", "threat": "Very High", "desc": "Features a projection barrier absorbing kinetic damage. Players must deplete the outer energy shield before reaching the primary hull."},
            "8": {"name": "NOVA DESTROYER", "class": "Heavy Destroyer", "hp": "4", "threat": "Extreme", "desc": "A massive heavy fighter. Spawns direct laser channels using high-density amber fuel rods. Armor is remarkably thick."},
            "SENTINEL-X": {"name": "SENTINEL-X / MK-2", "class": "Vanguard Mid-Boss", "hp": "50/80/120", "threat": "Extreme", "desc": "Fast reconnaissance flagship. Runs a twin synchronized energy matrix and localized heavy armor plating. Upgrades in Galaxy 2."},
            "VOID REAVER": {"name": "VOID REAVER", "class": "Vanguard Mid-Boss", "hp": "90/135/180", "threat": "Fatal", "desc": "An ancient energy absorber. Synthesizes slow-tracking void spheres and breaches security to summon interceptors."},
            "LEVIATHAN ETERNAL": {"name": "LEVIATHAN ETERNAL", "class": "Galaxy 1 Overlord", "hp": "160", "threat": "Apocalypse", "desc": "The first central mothership core. Armed with rotating orbital generators, vector cannons and automated battle sub-phases."},
            "OVERLORD": {"name": "OVERLORD DREADNOUGHT", "class": "Galaxy 2 Overlord", "hp": "220", "threat": "Apocalypse", "desc": "Heavy command dreadnought of the Andromeda fleet. Employs twin heavy-charge particle cannons that sweep vertical sectors and sweeps diagonal fire."},
            "BIG BOSS": {"name": "BIG BOSS", "class": "Galaxy 3 Overlord", "hp": "300", "threat": "Cataclysmic", "desc": "TMWSTW"}
        }
        self.glossary_keys = list(self.glossary_database.keys())

    def load_unlocks(self):
        if os.path.exists(self.unlocked_filename):
            try:
                with open(self.unlocked_filename, 'r') as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def save_unlocks(self):
        try:
            with open(self.unlocked_filename, 'w') as f:
                json.dump(list(self.unlocked_entries), f)
        except Exception as e:
            print(f"Ошибка сохранения разблокировок: {e}")

    def unlock_entity(self, key):
        if key not in self.unlocked_entries:
            self.unlocked_entries.add(key)
            self.save_unlocks()
            floating_text.spawn(SCREEN_WIDTH // 2, 110, "TACTICAL INTEL SECURED!", COLOR_GOLD, 20)

    def create_crt_mask(self):
        mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(mask, (0, 0, 0, 30), (0, y), (SCREEN_WIDTH, y), 2)
        return mask

    def start_new_game(self):
        self.player = Player()
        diff = self.difficulty_settings[self.current_difficulty]
        self.player.max_hp = diff["player_hp"]
        self.player.hp = self.player.max_hp

        self.enemies.clear()
        self.enemy_lasers.clear()
        self.player_lasers.clear()
        self.powerups.clear()
        self.asteroids.clear()
        self.mines.clear()
        self.boss = None
        self.level = 1
        self.stage = 1
        self.freeplay_mode = False
        self.paused = False
        self.boss_spawned = False
        self.score_multiplier = 1.0
        self.combo_timer = 0
        self.state = "PLAYING"

        self.shop_prices = {
            'hull': 15, 'shield': 15, 'speed': 20, 'fire_rate': 25, 'weapon_level': 40, 'wingman': 60
        }
        self.starfield.regenerate_stars(self.level)
        self.load_level(self.level)

    def load_level(self, lvl):
        self.enemies.clear()
        self.enemy_lasers.clear()
        self.player_lasers.clear()
        self.asteroids.clear()
        self.mines.clear()
        self.boss = None
        self.boss_spawned = False

        cols = 8
        rows = 3
        for r in range(rows):
            for c in range(cols):
                tx = 150 + c * 70
                ty = 100 + r * 50

                if lvl == 1:
                    type_id = 1 if r >= 1 else 2
                elif lvl == 2:
                    type_id = random.choices([1, 2, 3, 5, 6, 7], weights=[25, 20, 20, 10, 12, 13])[0]
                else:
                    type_id = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[15, 15, 15, 10, 10, 15, 10, 10])[0]

                if type_id == 5:
                    self.enemies.append(EnemyBomber(c, r, tx, ty, game=self))
                else:
                    self.enemies.append(Enemy(c, r, tx, ty, type_id, game=self))

        floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, f"GALAXY {lvl} - STAGE {self.stage}", COLOR_GOLD, 26)

    def handle_upgrade_purchase(self, upgrade_type):
        cost = self.shop_prices.get(upgrade_type, 999)
        if self.player.scrap_collected >= cost:
            if upgrade_type == 'hull':
                self.player.max_hp += 1
                self.player.hp = self.player.max_hp
                self.player.scrap_collected -= cost
                sfx.play('powerup')
                self.shop_prices['hull'] = int(cost * 1.5)
            elif upgrade_type == 'shield':
                self.player.max_shield += 25
                self.player.shield = self.player.max_shield
                self.player.scrap_collected -= cost
                sfx.play('powerup')
                self.shop_prices['shield'] = int(cost * 1.5)
            elif upgrade_type == 'speed':
                self.player.speed += 0.8
                self.player.scrap_collected -= cost
                sfx.play('powerup')
                self.shop_prices['speed'] = int(cost * 1.6)
            elif upgrade_type == 'fire_rate':
                self.player.fire_rate_modifier += 1
                self.player.scrap_collected -= cost
                sfx.play('powerup')
                self.shop_prices['fire_rate'] = int(cost * 1.7)
            elif upgrade_type == 'weapon_level':
                if self.player.base_weapon_level < 3:
                    self.player.base_weapon_level += 1
                    self.player.weapon_level = max(self.player.weapon_level, self.player.base_weapon_level)
                    self.player.scrap_collected -= cost
                    sfx.play('powerup')
                    self.shop_prices['weapon_level'] = int(cost * 2.2)
                else:
                    floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, "MAX WEAPON LEVEL REACHED", COLOR_RED, 18)
            elif upgrade_type == 'wingman':
                if len(self.player.drones) < 2:
                    self.player.add_wingman()
                    self.player.scrap_collected -= cost
                    sfx.play('powerup')
                    self.shop_prices['wingman'] = cost * 2
                else:
                    floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, "MAX DRONES REACHED", COLOR_RED, 18)

    def trigger_casino_spin(self):
        if self.player.scrap_collected >= 10 and self.casino_spin_timer == 0:
            self.player.scrap_collected -= 10
            self.casino_spin_timer = self.casino_spin_duration
            self.casino_result_text = "SPINNING BARRELS..."
            self.casino_result_color = COLOR_WHITE
            sfx.play('click')
        elif self.casino_spin_timer == 0:
            self.casino_result_text = "NOT ENOUGH SCRAP METAL!"
            self.casino_result_color = COLOR_RED
            sfx.play('slot_lose')

    def calculate_casino_result(self):
        r1, r2, r3 = self.casino_reels
        if r1 == "X" and r2 == "X" and r3 == "X":
            self.casino_result_text = "CURSED COILS! -10 SCRAP & -1 HP"
            self.casino_result_color = COLOR_RED
            self.player.scrap_collected = max(0, self.player.scrap_collected - 10)
            self.player.damage(1)
            sfx.play('slot_lose')
            camera_shake.trigger(10, 15)
        elif r1 == "$" and r2 == "$" and r3 == "$":
            self.casino_result_text = "MEGA JACKPOT! +50 SCRAP METAL"
            self.casino_result_color = COLOR_GOLD
            self.player.scrap_collected += 50
            sfx.play('slot_win')
        elif r1 == "S" and r2 == "S" and r3 == "S":
            self.casino_result_text = "SHIELD MATRIX REGENERATED!"
            self.casino_result_color = COLOR_GREEN
            self.player.hp = self.player.max_hp
            self.player.shield = self.player.max_shield
            sfx.play('slot_win')
        elif r1 == "W" and r2 == "W" and r3 == "W":
            self.casino_result_text = "ARSENAL UPGRADED! (15s Boost)"
            self.casino_result_color = COLOR_CYAN
            self.player.weapon_level = 3
            self.player.weapon_upgrade_timer = 900
            self.player.add_wingman()
            sfx.play('slot_win')
        elif r1 == "C" and r2 == "C" and r3 == "C":
            self.casino_result_text = "CARGO CONTAINER ACQUIRED! +30 SCRAP"
            self.casino_result_color = COLOR_YELLOW
            self.player.scrap_collected += 30
            sfx.play('slot_win')
        elif (r1 == r2 or r2 == r3 or r1 == r3) and ("X" not in [r1, r2, r3]):
            self.casino_result_text = "STABLE SYNERGY! +15 SCRAP"
            self.casino_result_color = COLOR_GOLD
            self.player.scrap_collected += 15
            sfx.play('powerup')
        else:
            self.casino_result_text = "NO COMBINATION. TRY AGAIN!"
            self.casino_result_color = COLOR_GREY
            sfx.play('slot_lose')

    def enable_freeplay_mode(self):
        self.freeplay_mode = True
        self.state = "GALAXY_TRANSITION"
        self.transition_timer = 180
        sfx.play('powerup')

    def update(self):
        if self.state == "GALAXY_TRANSITION":
            self.starfield.update(speed_multiplier=12.0)
            effects.update()
            effects.spawn_spark(self.player.x, self.player.y + 15, random.uniform(-4, 4), random.uniform(6, 12), COLOR_CYAN)
            effects.spawn_spark(self.player.x, self.player.y + 15, random.uniform(-2, 2), random.uniform(4, 9), COLOR_BLUE)
            self.player.y -= 1.8

            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.level += 1
                self.stage = 0
                self.starfield.regenerate_stars(self.level)
                self.state = "HANGAR"
            return

        self.starfield.update(speed_multiplier=3.5 if self.state == "PLAYING" else 1.0)
        camera_shake.update()
        floating_text.update()

        if self.state == "CASINO" and self.casino_spin_timer > 0:
            self.casino_spin_timer -= 1
            if self.casino_spin_timer % 4 == 0:
                sfx.play('slot_tick')
                if self.casino_spin_timer > 60:
                    self.casino_reels[0] = random.choice(self.casino_symbols)
                if self.casino_spin_timer > 35:
                    self.casino_reels[1] = random.choice(self.casino_symbols)
                if self.casino_spin_timer > 0:
                    self.casino_reels[2] = random.choice(self.casino_symbols)
            if self.casino_spin_timer == 0:
                self.calculate_casino_result()

        if self.state != "PLAYING" or self.paused:
            return

        self.player.update(self.player_lasers)
        effects.update()

        if self.player.magnet_timer > 0:
            for p in self.powerups:
                dx = self.player.x - p.x
                dy = self.player.y - p.y
                dist = math.hypot(dx, dy)
                if dist < 250:
                    p.x += (dx / dist) * 6.5
                    p.y += (dy / dist) * 6.5

        time_scale = 0.3 if self.player.time_slow_timer > 0 else 1.0

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.score_multiplier = 1.0

        if not self.boss and random.random() < 0.008 * time_scale:
            self.asteroids.append(Asteroid())

        for a in self.asteroids[:]:
            a.update(time_scale)
            if a.y > SCREEN_HEIGHT + 40:
                self.asteroids.remove(a)

        for l in self.player_lasers[:]:
            l.update()
            if l.y < -20 or l.y > SCREEN_HEIGHT + 20:
                self.player_lasers.remove(l)

        for l in self.enemy_lasers[:]:
            l.update()
            if l.y > SCREEN_HEIGHT + 20 or l.y < -20:
                self.enemy_lasers.remove(l)

        for m in self.mines[:]:
            m.update(time_scale)
            if m.y > SCREEN_HEIGHT + 20:
                self.mines.remove(m)

        for p in self.powerups[:]:
            p.update()
            if p.life <= 0 or p.y > SCREEN_HEIGHT + 20:
                self.powerups.remove(p)

        if len(self.enemies) > 0 and random.random() < 0.015 * time_scale:
            cand = random.choice(self.enemies)
            if cand.state == "grid":
                cand.start_dive(self.player.x)

        for e in self.enemies[:]:
            res = e.update(self.player.x, self.enemy_lasers, time_scale)
            if res == "spawn_mine":
                self.mines.append(SpaceMine(e.x, e.y + 15))

        if len(self.enemies) == 0 and not self.boss_spawned:
            if self.stage == 2:
                self.boss = BossSentinel(game=self)
                if self.level == 1:
                    self.boss.hp = 50
                    self.boss.max_hp = 50
                    self.boss.name = "SENTINEL-X"
                elif self.level == 2:
                    self.boss.hp = 80
                    self.boss.max_hp = 80
                    self.boss.name = "SENTINEL MK-2"
                elif self.level >= 3:
                    self.boss.hp = 120 + (self.level - 3) * 30
                    self.boss.max_hp = self.boss.hp
                    self.boss.name = f"GOLIATH SENTINEL MK-{self.level - 1}"
                self.boss_spawned = True
                sfx.play('boss_shoot')
                floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, f"VANGUARD INCOMING: {self.boss.name}", COLOR_RED, 22)

            elif self.stage == 4:
                self.boss = BossVoidReaver(game=self)
                if self.level == 1:
                    self.boss.hp = 90
                    self.boss.max_hp = 90
                    self.boss.name = "VOID REAVER"
                elif self.level == 2:
                    self.boss.hp = 135
                    self.boss.max_hp = 135
                    self.boss.name = "REAVER VOIDBORN"
                elif self.level >= 3:
                    self.boss.hp = 180 + (self.level - 3) * 40
                    self.boss.max_hp = self.boss.hp
                    self.boss.name = f"REAVER APEX MK-{self.level - 1}"
                self.boss_spawned = True
                sfx.play('boss_shoot')
                floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, f"GUARDIAN INCOMING: {self.boss.name}", COLOR_RED, 22)

            elif self.stage == 5:
                if self.level == 1:
                    self.boss = BossLeviathan(game=self)
                elif self.level == 2:
                    self.boss = BossOverlord(game=self)
                elif self.level >= 3:
                    self.boss = BossAetherius(game=self)
                    if self.level > 3:
                        self.boss.hp = 300 + (self.level - 3) * 60
                        self.boss.max_hp = self.boss.hp
                        self.boss.name = f"AETHERIUS MK-{self.level - 2}"
                self.boss_spawned = True
                sfx.play('boss_shoot')
                floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, f"ULTIMATE TARGET ENGAGED: {self.boss.name}", COLOR_RED, 22)

        if self.boss:
            self.boss.update(self.player.x, self.enemy_lasers, self.enemies, time_scale)

        self.check_collisions()

        level_cleared = False
        if len(self.enemies) == 0:
            if self.stage in [2, 4, 5]:
                if self.boss_spawned and not self.boss:
                    level_cleared = True
            else:
                level_cleared = True

        if level_cleared:
            if self.stage == 5:
                if self.level < self.max_levels or self.freeplay_mode:
                    self.state = "GALAXY_TRANSITION"
                    self.transition_timer = 180
                    sfx.play('powerup')
                else:
                    self.leaderboard.add_score(self.player.score)
                    self.state = "VICTORY"
            else:
                self.state = "STAGE_CLEAR"
                sfx.play('powerup')

    def check_collisions(self):
        for l in self.player_lasers[:]:
            for e in self.enemies[:]:
                if l.get_rect().colliderect(e.get_rect()):
                    if e.shield > 0:
                        e.shield -= l.damage
                        effects.spawn_explosion(l.x, l.y, [COLOR_CYAN, COLOR_BLUE], 6)
                        if l in self.player_lasers: self.player_lasers.remove(l)
                        break

                    e.hp -= l.damage
                    effects.spawn_explosion(l.x, l.y, [e.color, COLOR_WHITE], 8, (1, 4))
                    if l in self.player_lasers: self.player_lasers.remove(l)

                    if e.hp <= 0:
                        sfx.play('explosion')
                        effects.spawn_explosion(e.x, e.y, [e.color, COLOR_ORANGE, COLOR_WHITE], 22)
                        self.combo_timer = 150
                        earned_score = int(e.score_value * self.score_multiplier)
                        self.player.score += earned_score

                        floating_text.spawn(e.x, e.y, f"+{earned_score}", COLOR_WHITE, 16)
                        if self.score_multiplier > 1.0:
                            floating_text.spawn(e.x, e.y + 16, f"{self.score_multiplier:.1f}x Combo!", COLOR_YELLOW, 12)
                        self.score_multiplier = min(4.0, self.score_multiplier + 0.2)

                        if random.random() < 0.35:
                            self.powerups.append(PowerUp(e.x, e.y))
                        self.enemies.remove(e)
                    break

        for l in self.player_lasers[:]:
            for m in self.mines[:]:
                if l.get_rect().colliderect(m.get_rect()):
                    effects.spawn_explosion(m.x, m.y, [COLOR_RED, COLOR_WHITE], 15)
                    sfx.play('explosion')
                    if l in self.player_lasers: self.player_lasers.remove(l)
                    self.mines.remove(m)
                    break

        for l in self.player_lasers[:]:
            for a in self.asteroids[:]:
                if l.get_rect().colliderect(a.get_rect()):
                    a.hp -= l.damage
                    effects.spawn_explosion(l.x, l.y, [COLOR_GREY, COLOR_WHITE], 6)
                    if l in self.player_lasers: self.player_lasers.remove(l)

                    if a.hp <= 0:
                        sfx.play('explosion')
                        effects.spawn_explosion(a.x, a.y, [COLOR_GREY, COLOR_WHITE], 20)
                        self.player.score += 50
                        if random.random() < 0.60:
                            self.powerups.append(PowerUp(a.x, a.y, type_id=4))
                        self.asteroids.remove(a)
                    break

        if self.boss:
            for l in self.player_lasers[:]:
                hit_shield = False
                if hasattr(self.boss, 'shield_active') and self.boss.shield_active:
                    for orb in self.boss.orbs:
                        orb_r = pygame.Rect(orb.x - 16, orb.y - 16, 32, 32)
                        if l.get_rect().colliderect(orb_r):
                            orb.hp -= l.damage
                            effects.spawn_explosion(l.x, l.y, [COLOR_CYAN, COLOR_WHITE], 8)
                            if l in self.player_lasers: self.player_lasers.remove(l)
                            hit_shield = True
                            break
                if hit_shield:
                    continue

                if l.get_rect().colliderect(self.boss.get_rect()):
                    if l in self.player_lasers: self.player_lasers.remove(l)
                    if hasattr(self.boss, 'shield_active') and self.boss.shield_active:
                        effects.spawn_explosion(l.x, l.y, [COLOR_CYAN, COLOR_BLUE], 12)
                    else:
                        self.boss.hp -= l.damage
                        effects.spawn_explosion(l.x, l.y, [COLOR_RED, COLOR_WHITE], 10)
                        camera_shake.trigger(3, 4)
                        if self.boss.hp <= 0:
                            sfx.play('explosion')
                            effects.spawn_explosion(self.boss.x, self.boss.y, [COLOR_RED, COLOR_YELLOW, COLOR_WHITE], 70)
                            self.boss = None
                    break

        for l in self.enemy_lasers[:]:
            if l.get_rect().colliderect(self.player.get_rect()):
                if l in self.enemy_lasers: self.enemy_lasers.remove(l)
                dead = self.player.damage(l.damage)
                if dead:
                    sfx.play('death')
                    self.leaderboard.add_score(self.player.score)
                    self.state = "GAMEOVER"
                break

        for m in self.mines[:]:
            if m.get_rect().colliderect(self.player.get_rect()):
                effects.spawn_explosion(m.x, m.y, [COLOR_RED, COLOR_WHITE], 30)
                if m in self.mines: self.mines.remove(m)
                dead = self.player.damage(2)
                if dead:
                    sfx.play('death')
                    self.leaderboard.add_score(self.player.score)
                    self.state = "GAMEOVER"
                break

        for a in self.asteroids[:]:
            if a.get_rect().colliderect(self.player.get_rect()):
                effects.spawn_explosion(a.x, a.y, [COLOR_GREY, COLOR_WHITE], 25)
                if a in self.asteroids: self.asteroids.remove(a)
                dead = self.player.damage(2)
                if dead:
                    sfx.play('death')
                    self.leaderboard.add_score(self.player.score)
                    self.state = "GAMEOVER"
                break

        for e in self.enemies[:]:
            if e.get_rect().colliderect(self.player.get_rect()):
                effects.spawn_explosion(e.x, e.y, [e.color, COLOR_WHITE], 20)
                if e in self.enemies: self.enemies.remove(e)
                dead = self.player.damage(1)
                if dead:
                    sfx.play('death')
                    self.leaderboard.add_score(self.player.score)
                    self.state = "GAMEOVER"
                break

        for p in self.powerups[:]:
            if p.get_rect().colliderect(self.player.get_rect()):
                sfx.play('powerup')
                if p.type_id == 1:
                    self.player.weapon_level = min(3, self.player.weapon_level + 1)
                    self.player.weapon_upgrade_timer = 600
                    floating_text.spawn(self.player.x, self.player.y - 20, "WEAPONS UPGRADED (10s Boost)", COLOR_CYAN, 16)
                elif p.type_id == 2:
                    self.player.shield = min(self.player.max_shield, self.player.shield + 50)
                    floating_text.spawn(self.player.x, self.player.y - 20, "SHIELD CHARGED", COLOR_GREEN, 16)
                elif p.type_id == 4:
                    self.player.scrap_collected += 5
                    floating_text.spawn(self.player.x, self.player.y - 20, "+5 Scrap Metal", COLOR_GOLD, 14)
                elif p.type_id == 5:
                    self.player.double_damage_timer = 300
                    floating_text.spawn(self.player.x, self.player.y - 20, "DOUBLE DAMAGE!", COLOR_MAGENTA, 16)
                elif p.type_id == 6:
                    self.player.time_slow_timer = 300
                    floating_text.spawn(self.player.x, self.player.y - 20, "TIME SLOW ACTIVE", COLOR_BLUE, 16)
                elif p.type_id == 7:
                    self.player.magnet_timer = 420
                    floating_text.spawn(self.player.x, self.player.y - 20, "MATTER MAGNET ACTIVE", COLOR_ORANGE, 16)
                if p in self.powerups: self.powerups.remove(p)

    def draw(self, surface):
        sh_x, sh_y = camera_shake.get_offset()
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.fill(COLOR_BLACK)

        self.starfield.draw(temp_surface)

        if self.state in ["PLAYING", "STAGE_CLEAR", "GALAXY_TRANSITION"]:
            for a in self.asteroids: a.draw(temp_surface)
            for m in self.mines: m.draw(temp_surface)
            for l in self.player_lasers: l.draw(temp_surface)
            for l in self.enemy_lasers: l.draw(temp_surface)
            for e in self.enemies: e.draw(temp_surface)
            if self.boss: self.boss.draw(temp_surface)
            for p in self.powerups: p.draw(temp_surface)

            self.player.draw(temp_surface)
            effects.draw(temp_surface)
            floating_text.draw(temp_surface)
            self.draw_hud(temp_surface)

            if self.paused: self.draw_pause_overlay(temp_surface)
            if self.state == "STAGE_CLEAR": self.draw_stage_clear_overlay(temp_surface)
            if self.state == "GALAXY_TRANSITION": self.draw_galaxy_transition_overlay(temp_surface)

        elif self.state == "MENU": self.draw_menu_screen(temp_surface)
        elif self.state == "DIFFICULTY_SELECT": self.draw_difficulty_screen(temp_surface)
        elif self.state == "HANGAR": self.draw_hangar_screen(temp_surface)
        elif self.state == "CASINO": self.draw_casino_screen(temp_surface)
        elif self.state == "GAMEOVER": self.draw_game_over_screen(temp_surface)
        elif self.state == "VICTORY": self.draw_victory_screen(temp_surface)
        elif self.state == "INSTRUCTIONS": self.draw_instructions_screen(temp_surface)
        elif self.state == "LEADERBOARD": self.leaderboard.draw(temp_surface, self.draw_button)

        temp_surface.blit(self.crt_overlay, (0, 0))
        surface.blit(temp_surface, (sh_x, sh_y))
        pygame.display.flip()

    def draw_hud(self, surface):
        font = pygame.font.SysFont("Courier New", 18, bold=True)
        score_lbl = font.render(f"SCORE: {self.player.score:06d}", True, COLOR_WHITE)
        surface.blit(score_lbl, (20, 20))

        if self.score_multiplier > 1.0:
            combo_lbl = font.render(f"COMBO: {self.score_multiplier:.1f}x", True, COLOR_YELLOW)
            surface.blit(combo_lbl, (20, 42))

        y_offset = 64
        if self.player.double_damage_timer > 0:
            dd_lbl = font.render(f"DBL DMG: {self.player.double_damage_timer // 60}s", True, COLOR_MAGENTA)
            surface.blit(dd_lbl, (20, y_offset))
            y_offset += 20
        if self.player.time_slow_timer > 0:
            ts_lbl = font.render(f"TIME SLOW: {self.player.time_slow_timer // 60}s", True, COLOR_BLUE)
            surface.blit(ts_lbl, (20, y_offset))
            y_offset += 20
        if self.player.magnet_timer > 0:
            mg_lbl = font.render(f"MAGNET: {self.player.magnet_timer // 60}s", True, COLOR_ORANGE)
            surface.blit(mg_lbl, (20, y_offset))
            y_offset += 20
        if self.player.weapon_level > self.player.base_weapon_level:
            wpn_sec = self.player.weapon_upgrade_timer // 60
            wpn_timer_lbl = font.render(f"WPN BOOST: {wpn_sec}s", True, COLOR_CYAN)
            surface.blit(wpn_timer_lbl, (20, y_offset))

        lvl_lbl = font.render(f"GALAXY: {self.level}" if self.freeplay_mode else f"GALAXY: {self.level}/{self.max_levels}", True, COLOR_MAGENTA)
        surface.blit(lvl_lbl, (SCREEN_WIDTH - 150, 20))
        stage_lbl = font.render(f"STAGE: {self.stage}/{self.max_stages}", True, COLOR_CYAN)
        surface.blit(stage_lbl, (SCREEN_WIDTH - 150, 42))
        scrap_lbl = font.render(f"SCRAP: {self.player.scrap_collected:02d}", True, COLOR_GOLD)
        surface.blit(scrap_lbl, (SCREEN_WIDTH - 150, 64))

        hp_lbl = font.render("HULL:", True, COLOR_WHITE)
        surface.blit(hp_lbl, (20, SCREEN_HEIGHT - 35))
        for i in range(self.player.max_hp):
            color = COLOR_RED if i < self.player.hp else COLOR_DARK_GREY
            pygame.draw.circle(surface, color, (95 + i * 20, SCREEN_HEIGHT - 26), 7)

        shield_lbl = font.render("SHIELD:", True, COLOR_WHITE)
        surface.blit(shield_lbl, (220, SCREEN_HEIGHT - 35))
        pygame.draw.rect(surface, COLOR_DARK_GREY, (305, SCREEN_HEIGHT - 31, 120, 12), border_radius=3)
        if self.player.shield > 0:
            pct = self.player.shield / self.player.max_shield
            pygame.draw.rect(surface, COLOR_GREEN, (305, SCREEN_HEIGHT - 31, int(120 * pct), 12), border_radius=3)

        wpn_names = {1: "SINGLE L-1", 2: "DOUBLE L-2", 3: "BLAST STRIKE"}
        wpn_text = f"WEAPON: {wpn_names.get(self.player.weapon_level, 'MAX')}"
        wpn_lbl = font.render(wpn_text, True, COLOR_CYAN)
        surface.blit(wpn_lbl, (SCREEN_WIDTH - 240, SCREEN_HEIGHT - 35))

        if self.boss:
            self.boss.draw_health_bar(surface)

    def draw_pause_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))
        p_font = pygame.font.SysFont("Courier New", 36, bold=True)
        p_lbl = p_font.render("SIMULATION SUSPENDED", True, COLOR_YELLOW)
        surface.blit(p_lbl, (SCREEN_WIDTH // 2 - p_lbl.get_width() // 2, SCREEN_HEIGHT // 2 - 120))
        self.draw_button(surface, "RESUME SIMULATION", SCREEN_HEIGHT // 2 - 20, 0, size=(280, 45))
        self.draw_button(surface, "ABORT MISSION (QUIT)", SCREEN_HEIGHT // 2 + 45, 1, size=(280, 45))

    def handle_pause_clicks(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 20, 280, 45).collidepoint(mx, my):
            sfx.play('click')
            self.paused = False
        elif pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 45, 280, 45).collidepoint(mx, my):
            sfx.play('click')
            self.paused = False
            self.state = "MENU"

    def draw_stage_clear_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))
        t_font = pygame.font.SysFont("Courier New", 48, bold=True)
        lbl_font = pygame.font.SysFont("Courier New", 20, bold=True)

        title = t_font.render(f"STAGE {self.stage} COMPLETED", True, COLOR_GREEN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))
        scrap_info = lbl_font.render(f"CURRENT SCRAP BALANCE: {self.player.scrap_collected} UNITS", True, COLOR_GOLD)
        surface.blit(scrap_info, (SCREEN_WIDTH // 2 - scrap_info.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
        diff_info = lbl_font.render(f"GALAXY: {self.level} | STAGE: {self.stage}", True, COLOR_WHITE)
        surface.blit(diff_info, (SCREEN_WIDTH // 2 - diff_info.get_width() // 2, SCREEN_HEIGHT // 2))

        self.draw_button(surface, "PRESS SPACE FOR HANGAR BAY", SCREEN_HEIGHT // 2 + 80, 0, size=(340, 48))

    def draw_galaxy_transition_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        t_font = pygame.font.SysFont("Courier New", 44, bold=True)
        sub_font = pygame.font.SysFont("Courier New", 20, bold=True)
        galaxy_names = {2: "ANDROMEDA ABYSS (VIOLET NEBULA)", 3: "CENTAURI CORE (AMBER CORE)"}
        next_gal = galaxy_names.get(self.level + 1, "UNKNOWN DEEP SPACE")

        title = t_font.render("WARP MATRIX ENGAGED", True, COLOR_CYAN)
        sub_title1 = sub_font.render("HYPERSPACE JUMP IN PROGRESS...", True, COLOR_WHITE)
        sub_title2 = sub_font.render(f"LEAVING GALAXY {self.level} -> TRANSITING TO {next_gal}", True, COLOR_MAGENTA)

        if (self.transition_timer // 10) % 2 == 0:
            surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 150))
        surface.blit(sub_title1, (SCREEN_WIDTH // 2 - sub_title1.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        surface.blit(sub_title2, (SCREEN_WIDTH // 2 - sub_title2.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def handle_stage_clear_keys(self):
        self.state = "HANGAR"

    def draw_menu_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 54, bold=True)
        sub_font = pygame.font.SysFont("Courier New", 18, bold=True)
        pulse = int(140 + math.sin(pygame.time.get_ticks() * 0.005) * 115)
        color = (pulse, 50, 255)

        title = t_font.render("AVENGERS", True, color)
        sub_title = t_font.render("PROJECT", True, COLOR_CYAN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 110))
        surface.blit(sub_title, (SCREEN_WIDTH // 2 - sub_title.get_width() // 2, 170))

        self.draw_button(surface, "1. START MISSION", SCREEN_HEIGHT // 2 - 50, 0, size=(320, 44))
        self.draw_button(surface, "2. OPERATION MANUAL", SCREEN_HEIGHT // 2 + 10, 2, size=(320, 44))
        self.draw_button(surface, "3. LEADERBOARD", SCREEN_HEIGHT // 2 + 70, 3, size=(320, 44))
        self.draw_button(surface, "4. SHUT DOWN", SCREEN_HEIGHT // 2 + 130, 4, size=(320, 44))

        mute_info = sub_font.render("PRESS 'M' TO TOGGLE MUSIC", True, COLOR_DARK_GREY)
        surface.blit(mute_info, (SCREEN_WIDTH // 2 - mute_info.get_width() // 2, SCREEN_HEIGHT - 75))

        cp = sub_font.render("PRODUCED BY KRUTYE REBYATA", True, COLOR_GREY)
        surface.blit(cp, (SCREEN_WIDTH // 2 - cp.get_width() // 2, SCREEN_HEIGHT - 45))

    def draw_button(self, surface, text, y, index, size=(320, 48)):
        font = pygame.font.SysFont("Courier New", 18, bold=True)
        mx, my = pygame.mouse.get_pos()
        rect = pygame.Rect(SCREEN_WIDTH // 2 - size[0] // 2, y, size[0], size[1])

        hovered = rect.collidepoint(mx, my)
        bg = (30, 34, 46) if hovered else (14, 16, 22)
        border = COLOR_CYAN if hovered else COLOR_GREY

        pygame.draw.rect(surface, bg, rect, border_radius=6)
        pygame.draw.rect(surface, border, rect, 2, border_radius=6)
        txt_s = font.render(text, True, COLOR_WHITE if hovered else COLOR_GREY)
        surface.blit(txt_s, (SCREEN_WIDTH // 2 - txt_s.get_width() // 2, y + size[1] // 2 - txt_s.get_height() // 2))

    def handle_menu_clicks(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 50, 320, 44).collidepoint(mx, my):
            sfx.play('click')
            self.state = "DIFFICULTY_SELECT"
        elif pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 10, 320, 44).collidepoint(mx, my):
            sfx.play('click')
            self.state = "INSTRUCTIONS"
        elif pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 70, 320, 44).collidepoint(mx, my):
            sfx.play('click')
            self.state = "LEADERBOARD"
        elif pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 130, 320, 44).collidepoint(mx, my):
            sfx.play('click')
            pygame.quit()
            import sys
            sys.exit()

    def draw_difficulty_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 36, bold=True)
        desc_font = pygame.font.SysFont("Courier New", 16, bold=True)

        title = t_font.render("SELECT COMBAT INTENSITY", True, COLOR_CYAN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        self.draw_button(surface, "EASY INFILTRATION", 200, 0, size=(300, 45))
        self.draw_button(surface, "STANDARD PROTOCOL", 320, 1, size=(300, 45))
        self.draw_button(surface, "HARDCORE ONSLAUGHT", 440, 2, size=(300, 45))

        d1 = desc_font.render("Enemy Armor: 0.7x | Speed: 0.7x | Hull HP: 4", True, COLOR_GREEN)
        d2 = desc_font.render("Enemy Armor: 1.0x | Speed: 1.0x | Hull HP: 3", True, COLOR_YELLOW)
        d3 = desc_font.render("Enemy Armor: 1.35x| Speed: 1.25x| Hull HP: 2", True, COLOR_RED)

        surface.blit(d1, (SCREEN_WIDTH // 2 - d1.get_width() // 2, 260))
        surface.blit(d2, (SCREEN_WIDTH // 2 - d2.get_width() // 2, 380))
        surface.blit(d3, (SCREEN_WIDTH // 2 - d3.get_width() // 2, 500))
        self.draw_button(surface, "RETURN TO MAIN MENU", 620, 3, size=(280, 45))

    def handle_difficulty_clicks(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.Rect(SCREEN_WIDTH // 2 - 150, 200, 300, 45).collidepoint(mx, my):
            sfx.play('click')
            self.current_difficulty = "EASY"
            self.start_new_game()
        elif pygame.Rect(SCREEN_WIDTH // 2 - 150, 320, 300, 45).collidepoint(mx, my):
            sfx.play('click')
            self.current_difficulty = "NORMAL"
            self.start_new_game()
        elif pygame.Rect(SCREEN_WIDTH // 2 - 150, 440, 300, 45).collidepoint(mx, my):
            sfx.play('click')
            self.current_difficulty = "HARD"
            self.start_new_game()
        elif pygame.Rect(SCREEN_WIDTH // 2 - 140, 620, 280, 45).collidepoint(mx, my):
            sfx.play('click')
            self.state = "MENU"

    def draw_hangar_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 36, bold=True)
        lbl_font = pygame.font.SysFont("Courier New", 18, bold=True)

        title = t_font.render("ORBITAL HANGAR BAY", True, COLOR_CYAN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))
        scrap_lbl = lbl_font.render(f"AVAILABLE SCRAP METAL: {self.player.scrap_collected} UNITS", True, COLOR_GOLD)
        surface.blit(scrap_lbl, (SCREEN_WIDTH // 2 - scrap_lbl.get_width() // 2, 115))

        upgrades = [
            ('HULL PLATING (MAX HP+1)', 'hull', self.shop_prices['hull']),
            ('DEFLECTOR GENERATOR (SHIELD+25)', 'shield', self.shop_prices['shield']),
            ('THRUST INJECTORS (SPEED+)', 'speed', self.shop_prices['speed']),
            ('COOLING COILS (FIRE RATE+)', 'fire_rate', self.shop_prices['fire_rate']),
            ('WEAPON SYSTEMS (BASE LEVEL+)', 'weapon_level', self.shop_prices['weapon_level']),
            ('SUPPORT WINGMAN DRONE', 'wingman', self.shop_prices['wingman'])
        ]

        y_offset = 150
        for i, (name, upgrade_key, price) in enumerate(upgrades):
            self.draw_button(surface, f"{name} - {price} SCRAP", y_offset, i, size=(450, 40))
            y_offset += 55

        mx, my = pygame.mouse.get_pos()
        casino_rect = pygame.Rect(SCREEN_WIDTH // 2 - 225, y_offset, 450, 40)
        hovered = casino_rect.collidepoint(mx, my)

        time_ms = pygame.time.get_ticks()
        r = int(127 + 127 * math.sin(time_ms * 0.003))
        g = int(127 + 127 * math.sin(time_ms * 0.003 + 2.0))
        b = int(127 + 127 * math.sin(time_ms * 0.003 + 4.0))
        neon_color = (r, g, b)

        pulse_width = int(2 + abs(math.sin(time_ms * 0.005)) * 5)

        bg_color = (30, 15, 35) if hovered else (12, 6, 14)
        pygame.draw.rect(surface, bg_color, casino_rect, border_radius=6)

        for w in range(pulse_width, 0, -1):
            pygame.draw.rect(surface, neon_color, casino_rect.inflate(w * 2, w * 2), 1, border_radius=6)

        pygame.draw.rect(surface, neon_color, casino_rect, 2, border_radius=6)

        casino_txt = "ENTER SLOTS CASINO (10 Scrap)"
        txt_s = lbl_font.render(casino_txt, True, COLOR_WHITE if hovered else neon_color)
        surface.blit(txt_s, (SCREEN_WIDTH // 2 - txt_s.get_width() // 2, y_offset + 20 - txt_s.get_height() // 2))

        y_offset += 55
        self.draw_button(surface, "LAUNCH NEXT STAGE", SCREEN_HEIGHT - 90, 99, size=(300, 50))

    def handle_hangar_clicks(self):
        mx, my = pygame.mouse.get_pos()
        upgrades = ['hull', 'shield', 'speed', 'fire_rate', 'weapon_level', 'wingman']
        y_offset = 150
        for i, up_type in enumerate(upgrades):
            if pygame.Rect(SCREEN_WIDTH // 2 - 225, y_offset, 450, 40).collidepoint(mx, my):
                self.handle_upgrade_purchase(up_type)
                return
            y_offset += 55

        if pygame.Rect(SCREEN_WIDTH // 2 - 225, y_offset, 450, 40).collidepoint(mx, my):
            sfx.play('click')
            self.state = "CASINO"
            self.casino_result_text = "SPIN TO WIN OR LOSE!"
            self.casino_result_color = COLOR_WHITE
            return

        if pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 90, 300, 50).collidepoint(mx, my):
            sfx.play('click')
            self.stage += 1
            self.load_level(self.level)
            self.state = "PLAYING"

    def draw_casino_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 36, bold=True)
        sub_font = pygame.font.SysFont("Courier New", 20, bold=True)
        reel_font = pygame.font.SysFont("Courier New", 48, bold=True)

        title = t_font.render("GENESIS SPACE SLOTS", True, COLOR_MAGENTA)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        scrap_lbl = sub_font.render(f"YOUR SCRAP METAL: {self.player.scrap_collected} UNITS", True, COLOR_GOLD)
        surface.blit(scrap_lbl, (SCREEN_WIDTH // 2 - scrap_lbl.get_width() // 2, 130))

        frame_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 180, 400, 320)
        pygame.draw.rect(surface, (24, 25, 35), frame_rect, border_radius=12)
        neon_pulse = int(140 + math.sin(pygame.time.get_ticks() * 0.01) * 115)
        neon_color = (neon_pulse, 0, neon_pulse)
        pygame.draw.rect(surface, neon_color, frame_rect, 4, border_radius=12)

        for i in range(3):
            rx = SCREEN_WIDTH // 2 - 150 + i * 110
            ry = 220
            r_rect = pygame.Rect(rx, ry, 80, 120)
            pygame.draw.rect(surface, (10, 10, 15), r_rect, border_radius=8)
            pygame.draw.rect(surface, COLOR_GREY, r_rect, 2, border_radius=8)

            sym = self.casino_reels[i]
            sym_color = COLOR_GOLD if sym == "$" else (COLOR_GREEN if sym == "S" else (COLOR_CYAN if sym == "W" else (COLOR_YELLOW if sym == "C" else COLOR_WHITE)))
            sym_lbl = reel_font.render(sym, True, sym_color)
            surface.blit(sym_lbl, (rx + 40 - sym_lbl.get_width() // 2, ry + 60 - sym_lbl.get_height() // 2))

        res_lbl = sub_font.render(self.casino_result_text, True, self.casino_result_color)
        surface.blit(res_lbl, (SCREEN_WIDTH // 2 - res_lbl.get_width() // 2, 380))

        self.draw_button(surface, "SPIN BARRELS (10 Scrap)", 430, 0, size=(280, 45))
        self.draw_button(surface, "LEAVE CASINO", 540, 1, size=(280, 45))

        info_font = pygame.font.SysFont("Courier New", 14, bold=True)
        y_offset = 620
        combos = [
            "COMBINATIONS Payouts: ",
            "[$]-[$]-[$] Jackpot! +50 Scrap   | [S]-[S]-[S] Full Hull Recovery",
            "[W]-[W]-[W] Arsenal (15s Boost)  | [C]-[C]-[C] Cargo Container: +30 Scrap",
            "Any 2 Matching Symbols (except X): Synergy Bonus +15 Scrap"
        ]
        for line in combos:
            lbl = info_font.render(line, True, COLOR_GREY if "COMBINATIONS" in line else COLOR_WHITE)
            surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, y_offset))
            y_offset += 20

    def handle_casino_clicks(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.Rect(SCREEN_WIDTH // 2 - 140, 430, 280, 45).collidepoint(mx, my):
            self.trigger_casino_spin()
        elif pygame.Rect(SCREEN_WIDTH // 2 - 140, 540, 280, 45).collidepoint(mx, my) and self.casino_spin_timer == 0:
            sfx.play('click')
            self.state = "HANGAR"

    def draw_instructions_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 36, bold=True)
        b_font = pygame.font.SysFont("Courier New", 18, bold=True)

        title = t_font.render("COMMAND INTERFACE", True, COLOR_CYAN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        lines = [
            "  * MOVEMENT CONTROLS *",
            "  STEER CRAFT  : WASD / ARROW KEYS (2D Movement Enabled)",
            "  TRIGGER LASERS: SPACEBAR (HOLD)",
            "  PAUSE MATRIX : ESCAPE / MENU OVERLAY",
            "",
            "  * EXTRA-TERRESTRIAL SALVAGE *",
            "  DESTROY ENEMIES & ASTEROIDS TO COLLECT [Scrap Metal ($)].",
            "  VISIT THE HANGAR TO SPEND SCRAP OR PLAY IN CASINO.",
            "",
            "  * ACTIVE TIMED POWERUPS *",
            "  [W] WEAPONS BOOST (CYAN): TEMPORARY FIREPOWER UPGRADE (10s)",
            "  [D] DOUBLE DAMAGE (MAGENTA LASERS): 2x DAMAGE BOOST (5s)",
            "  [T] TIME DILATOR (BLUE): SLOWS ENEMY SHIPS AND WEAPONS (5s)",
            "  [M] MATTER MAGNET (ORANGE): DRAWS DROPS FROM DISTANCE (7s)"
        ]

        y_offset = 150
        for line in lines:
            col = COLOR_YELLOW if "*" in line else (COLOR_CYAN if "[" in line else COLOR_WHITE)
            lbl = b_font.render(line, True, col)
            surface.blit(lbl, (80, y_offset))
            y_offset += 28
        self.draw_button(surface, "RETURN TO MENU", SCREEN_HEIGHT - 110, 0)

    def draw_game_over_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 48, bold=True)
        b_font = pygame.font.SysFont("Courier New", 20, bold=True)

        title = t_font.render("HULL INTEGRITY ZERO", True, COLOR_RED)
        score = b_font.render(f"MISSION SCORE: {self.player.score:06d}", True, COLOR_WHITE)
        best = b_font.render(f"TOP REGISTERED SCORE: {self.leaderboard.scores[0]:06d}", True, COLOR_YELLOW)

        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))
        surface.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 290))
        surface.blit(best, (SCREEN_WIDTH // 2 - best.get_width() // 2, 330))
        self.draw_button(surface, "TRY AGAIN", SCREEN_HEIGHT // 2 + 40, 0)
        self.draw_button(surface, "ABANDON TO MENU", SCREEN_HEIGHT // 2 + 110, 1)

    def draw_victory_screen(self, surface):
        t_font = pygame.font.SysFont("Courier New", 48, bold=True)
        b_font = pygame.font.SysFont("Courier New", 22, bold=True)

        title = t_font.render("GALAXY LIBERATED!", True, COLOR_GREEN)
        score = b_font.render(f"TOTAL WAR SCORE: {self.player.score:06d} PTS", True, COLOR_WHITE)
        best = b_font.render(f"RECORD BENCHMARK: {self.leaderboard.scores[0]:06d} PTS", True, COLOR_GOLD)

        if random.random() < 0.18:
            effects.spawn_explosion(random.randint(100, 700), random.randint(100, 300), [COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, COLOR_PURPLE, COLOR_GOLD], 40)
        effects.update()
        effects.draw(surface)

        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))
        surface.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 290))
        surface.blit(best, (SCREEN_WIDTH // 2 - best.get_width() // 2, 330))
        self.draw_button(surface, "CONTINUE IN FREEPLAY", SCREEN_HEIGHT // 2 + 80, 0, size=(320, 48))
        self.draw_button(surface, "EXIT TO MAIN MENU", SCREEN_HEIGHT // 2 + 150, 1, size=(320, 48))