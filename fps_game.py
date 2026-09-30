"""
사실적인 1인칭 슈팅 게임 (Raycasting FPS)
WASD: 이동 | 마우스: 시점 조작 | 클릭: 사격 | R: 재장전 | Shift: 달리기
"""

import pygame
import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
FOV = math.radians(66)
HALF_FOV = FOV / 2
NUM_RAYS = 320
MAX_DEPTH = 20
WALL_HEIGHT_SCALE = 1.0

TILE = 1.0  # 월드 타일 크기

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 30, 30)
DARK_RED = (120, 15, 15)
GREEN = (30, 180, 30)
DARK_GREEN = (15, 100, 15)
BLUE = (40, 80, 200)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
YELLOW = (255, 220, 50)
ORANGE = (255, 140, 0)
BROWN = (139, 90, 43)
DARK_BROWN = (80, 50, 20)
CEILING_COLOR = (40, 40, 50)
FLOOR_COLOR = (60, 55, 50)

# 맵 (1=벽, 0=빈 공간, 2=다른 벽 텍스처)
MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,2,2,2,2,0,0,0,0,0,0,0,0,2,2,2,2,2,0,0,1],
    [1,0,0,2,0,0,0,2,0,0,0,0,0,0,0,0,2,0,0,0,2,0,0,1],
    [1,0,0,2,0,0,0,2,0,0,0,0,0,0,0,0,2,0,0,0,2,0,0,1],
    [1,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,1],
    [1,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,1],
    [1,0,0,2,2,2,0,2,2,2,2,0,0,2,2,2,2,0,2,2,2,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

MAP_H = len(MAP)
MAP_W = len(MAP[0])


def is_wall(x: float, y: float) -> bool:
    """월드 좌표가 벽인지 확인"""
    mx, my = int(x), int(y)
    if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
        return True
    return MAP[my][mx] != 0


def get_wall_type(x: float, y: float) -> int:
    mx, my = int(x), int(y)
    if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
        return 1
    return MAP[my][mx]


# ─────────────────────────────────────────────
# 사운드 생성 (절차적)
# ─────────────────────────────────────────────
def create_sounds():
    """간단한 사운드 효과 생성"""
    sample_rate = 22050
    sounds = {}

    # 총성 (노이즈 버스트)
    duration = 0.15
    n = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n):
        t = i / sample_rate
        decay = math.exp(-t * 30)
        noise = random.uniform(-1, 1) * decay
        val = int(max(-1, min(1, noise)) * 32767)
        buf += val.to_bytes(2, 'little', signed=True)
    sounds['shoot'] = pygame.mixer.Sound(buffer=bytes(buf))

    # 재장전
    duration = 0.3
    n = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n):
        t = i / sample_rate
        freq = 800 + 400 * math.sin(t * 20)
        val = int(math.sin(2 * math.pi * freq * t) * 0.3 * 32767 * math.exp(-t * 5))
        buf += val.to_bytes(2, 'little', signed=True)
    sounds['reload'] = pygame.mixer.Sound(buffer=bytes(buf))

    # 피격
    duration = 0.2
    n = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n):
        t = i / sample_rate
        decay = math.exp(-t * 15)
        freq = 200 - t * 500
        val = int(math.sin(2 * math.pi * freq * t) * decay * 0.5 * 32767)
        buf += val.to_bytes(2, 'little', signed=True)
    sounds['hit'] = pygame.mixer.Sound(buffer=bytes(buf))

    # 적 사망
    duration = 0.4
    n = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n):
        t = i / sample_rate
        decay = math.exp(-t * 8)
        freq = 300 - t * 400
        val = int(math.sin(2 * math.pi * freq * t) * decay * 0.4 * 32767)
        buf += val.to_bytes(2, 'little', signed=True)
    sounds['enemy_die'] = pygame.mixer.Sound(buffer=bytes(buf))

    # 발소리
    duration = 0.08
    n = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n):
        t = i / sample_rate
        decay = math.exp(-t * 40)
        noise = random.uniform(-1, 1) * decay * 0.3
        val = int(noise * 32767)
        buf += val.to_bytes(2, 'little', signed=True)
    sounds['step'] = pygame.mixer.Sound(buffer=bytes(buf))

    return sounds


# ─────────────────────────────────────────────
# 데이터 클래스
# ─────────────────────────────────────────────
@dataclass
class Bullet:
    x: float
    y: float
    dx: float
    dy: float
    speed: float = 15.0
    life: float = 2.0
    from_player: bool = True


@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: int


@dataclass
class Enemy:
    x: float
    y: float
    hp: float = 100.0
    max_hp: float = 100.0
    speed: float = 1.5
    state: str = "idle"  # idle, chase, attack, dead
    attack_cooldown: float = 0.0
    hit_flash: float = 0.0
    death_timer: float = 0.0
    alert_radius: float = 8.0
    attack_range: float = 6.0
    damage: float = 15.0
    last_seen_x: float = 0.0
    last_seen_y: float = 0.0
    patrol_angle: float = 0.0
    patrol_timer: float = 0.0


@dataclass
class Weapon:
    name: str = "Rifle"
    damage: float = 34.0
    fire_rate: float = 0.12  # 초당 발사 간격
    mag_size: int = 30
    ammo: int = 30
    reserve_ammo: int = 120
    reload_time: float = 1.8
    spread: float = 0.01  # 라디안
    recoil: float = 0.02
    is_reloading: bool = False
    reload_timer: float = 0.0
    fire_cooldown: float = 0.0
    muzzle_flash: float = 0.0


# ─────────────────────────────────────────────
# 게임 클래스
# ─────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("FPS Raycasting Shooter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.sounds = create_sounds()

        # 플레이어
        self.px = 12.0
        self.py = 10.0
        self.pa = 0.0  # 플레이어 각도
        self.player_hp = 100.0
        self.player_max_hp = 100.0
        self.player_speed = 3.5
        self.sprint_speed = 5.5
        self.player_radius = 0.25
        self.bob_phase = 0.0
        self.bob_amount = 0.0
        self.step_timer = 0.0

        # 무기
        self.weapon = Weapon()

        # 게임 상태
        self.bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.particles: List[Particle] = []
        self.score = 0
        self.kills = 0
        self.wave = 0
        self.game_over = False
        self.game_over_timer = 0.0
        self.wave_transition = 0.0
        self.damage_flash = 0.0
        self.heal_flash = 0.0

        # 마우스
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        self.mouse_sensitivity = 0.002

        # 스폰 적
        self.spawn_wave()

    def spawn_wave(self):
        """웨이브 스폰"""
        self.wave += 1
        num_enemies = min(3 + self.wave * 2, 15)
        for _ in range(num_enemies):
            # 플레이어에서 먼 위치에 스폰
            while True:
                ex = random.uniform(1.5, MAP_W - 1.5)
                ey = random.uniform(1.5, MAP_H - 1.5)
                dist = math.hypot(ex - self.px, ey - self.py)
                if dist > 5.0 and not is_wall(ex, ey):
                    break
            self.enemies.append(Enemy(x=ex, y=ey))
        self.wave_transition = 2.0

    def cast_ray(self, angle: float) -> Tuple[float, float, float, int]:
        """DDA 레이캐스팅"""
        dx = math.cos(angle)
        dy = math.sin(angle)

        map_x = int(self.px)
        map_y = int(self.py)

        delta_dist_x = abs(1.0 / dx) if dx != 0 else 1e30
        delta_dist_y = abs(1.0 / dy) if dy != 0 else 1e30

        if dx < 0:
            step_x = -1
            side_dist_x = (self.px - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.px) * delta_dist_x

        if dy < 0:
            step_y = -1
            side_dist_y = (self.py - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.py) * delta_dist_y

        hit = False
        side = 0
        wall_type = 1

        for _ in range(100):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAP_W or map_y < 0 or map_y >= MAP_H:
                hit = True
                wall_type = 1
                break

            if MAP[map_y][map_x] != 0:
                hit = True
                wall_type = MAP[map_y][map_x]
                break

        if side == 0:
            perp_dist = (side_dist_x - delta_dist_x)
        else:
            perp_dist = (side_dist_y - delta_dist_y)

        # 어안 렌즈 보정
        corrected_dist = perp_dist * math.cos(angle - self.pa)

        # 벽이 맞은 위치 (텍스처 좌표용)
        if side == 0:
            wall_x = self.py + perp_dist * dy
        else:
            wall_x = self.px + perp_dist * dx
        wall_x -= math.floor(wall_x)

        return corrected_dist, wall_x, side, wall_type

    def render_walls(self):
        """벽 렌더링"""
        strip_w = SCREEN_W // NUM_RAYS
        z_buffer = [MAX_DEPTH] * NUM_RAYS

        for i in range(NUM_RAYS):
            ray_angle = self.pa - HALF_FOV + (i / NUM_RAYS) * FOV
            dist, wall_x, side, wall_type = self.cast_ray(ray_angle)

            # 거리 기반 안개
            fog_factor = min(1.0, dist / MAX_DEPTH)

            # 벽 높이
            wall_h = int((SCREEN_H / max(dist, 0.01)) * WALL_HEIGHT_SCALE)
            wall_top = (SCREEN_H - wall_h) // 2 + int(self.bob_amount * 5)
            wall_bottom = wall_top + wall_h

            # 텍스처 좌표
            tex_x = int(wall_x * 64) % 64

            # 기본 색상
            if wall_type == 1:
                base_r, base_g, base_b = 140, 130, 120
            else:
                base_r, base_g, base_b = 100, 80, 60

            # 면 방향에 따른 밝기
            if side == 1:
                base_r = int(base_r * 0.7)
                base_g = int(base_g * 0.7)
                base_b = int(base_b * 0.7)

            # 안개 적용
            r = int(base_r * (1 - fog_factor * 0.8))
            g = int(base_g * (1 - fog_factor * 0.8))
            b = int(base_b * (1 - fog_factor * 0.8))

            # 수직 스트라이프 (텍스처 느낌)
            if tex_x % 8 < 1:
                r = int(r * 0.85)
                g = int(g * 0.85)
                b = int(b * 0.85)

            pygame.draw.rect(self.screen, (r, g, b),
                           (i * strip_w, wall_top, strip_w + 1, wall_h))

            z_buffer[i] = dist

        return z_buffer

    def render_floor_ceiling(self):
        """바닥과 천장 렌더링"""
        # 천장
        for y in range(SCREEN_H // 2):
            fog = y / (SCREEN_H // 2)
            r = int(40 * (1 - fog * 0.5))
            g = int(40 * (1 - fog * 0.5))
            b = int(50 * (1 - fog * 0.3))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

        # 바닥
        for y in range(SCREEN_H // 2, SCREEN_H):
            fog = (y - SCREEN_H // 2) / (SCREEN_H // 2)
            r = int(60 * (1 - fog * 0.3))
            g = int(55 * (1 - fog * 0.3))
            b = int(50 * (1 - fog * 0.3))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

    def render_enemies(self, z_buffer):
        """적 스프라이트 렌더링"""
        # 거리순 정렬 (먼 것부터)
        sorted_enemies = sorted(self.enemies,
                               key=lambda e: math.hypot(e.x - self.px, e.y - self.py),
                               reverse=True)

        for enemy in sorted_enemies:
            dx = enemy.x - self.px
            dy = enemy.y - self.py
            dist = math.hypot(dx, dy)

            if dist < 0.1 or dist > MAX_DEPTH:
                continue

            # 각도 계산
            angle = math.atan2(dy, dx) - self.pa
            # 각도 정규화
            while angle > math.pi:
                angle -= 2 * math.pi
            while angle < -math.pi:
                angle += 2 * math.pi

            if abs(angle) > HALF_FOV + 0.2:
                continue

            # 화면 위치
            screen_x = int((0.5 + angle / FOV) * SCREEN_W)

            # 스프라이트 크기
            sprite_h = int(SCREEN_H / dist * 0.8)
            sprite_w = int(sprite_h * 0.6)
            sprite_top = (SCREEN_H - sprite_h) // 2 + int(self.bob_amount * 5)

            # 안개
            fog_factor = min(1.0, dist / MAX_DEPTH)

            # 색상
            if enemy.state == "dead":
                # 사망 애니메이션
                death_progress = enemy.death_timer / 0.5
                sprite_h = int(sprite_h * (1 - death_progress * 0.5))
                sprite_top = int(sprite_top + sprite_h * death_progress * 0.3)
                r, g, b = 80, 20, 20
            elif enemy.hit_flash > 0:
                r, g, b = 255, 200, 200
            else:
                r, g, b = 180, 50, 50

            r = int(r * (1 - fog_factor * 0.7))
            g = int(g * (1 - fog_factor * 0.7))
            b = int(b * (1 - fog_factor * 0.7))

            # z-buffer 체크 후 렌더링
            strip_w = SCREEN_W // NUM_RAYS
            start_x = screen_x - sprite_w // 2
            end_x = screen_x + sprite_w // 2

            for sx in range(max(0, start_x), min(SCREEN_W, end_x)):
                ray_idx = int(sx / strip_w)
                if 0 <= ray_idx < NUM_RAYS:
                    if z_buffer[ray_idx] > dist:
                        # 간단한 실루엣
                        rel_x = (sx - start_x) / max(sprite_w, 1)
                        # 몸통 형태
                        if 0.2 < rel_x < 0.8:
                            pygame.draw.line(self.screen, (r, g, b),
                                           (sx, sprite_top), (sx, sprite_top + sprite_h))

            # 체력바
            if enemy.state != "dead" and dist < 10:
                bar_w = sprite_w
                bar_h = 4
                bar_x = screen_x - bar_w // 2
                bar_y = sprite_top - 10
                hp_ratio = enemy.hp / enemy.max_hp
                pygame.draw.rect(self.screen, DARK_RED, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(self.screen, RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    def render_weapon(self):
        """무기 렌더링 (뷰모델)"""
        if self.weapon.is_reloading:
            # 재장전 애니메이션
            progress = 1.0 - (self.weapon.reload_timer / self.weapon.reload_time)
            offset = int(math.sin(progress * math.pi) * 80)
        else:
            offset = 0

        # 반동
        recoil_offset = int(self.weapon.recoil * 500)

        gun_w = 200
        gun_h = 120
        gun_x = SCREEN_W // 2 - gun_w // 2
        gun_y = SCREEN_H - gun_h + 20 + offset + recoil_offset

        # 총 몸체
        pygame.draw.rect(self.screen, DARK_GRAY, (gun_x + 40, gun_y + 40, gun_w - 80, gun_h - 40))
        pygame.draw.rect(self.screen, GRAY, (gun_x + 50, gun_y + 30, gun_w - 100, 30))
        # 총구
        pygame.draw.rect(self.screen, BLACK, (gun_x + gun_w // 2 - 15, gun_y, 30, 40))
        # 손잡이
        pygame.draw.rect(self.screen, DARK_BROWN, (gun_x + 70, gun_y + 70, 40, 50))

        # 머즐 플래시
        if self.weapon.muzzle_flash > 0:
            flash_size = int(30 * self.weapon.muzzle_flash / 0.05)
            flash_x = gun_x + gun_w // 2
            flash_y = gun_y - 10
            pygame.draw.circle(self.screen, YELLOW, (flash_x, flash_y), flash_size)
            pygame.draw.circle(self.screen, ORANGE, (flash_x, flash_y), flash_size // 2)

    def render_hud(self):
        """HUD 렌더링"""
        # 체력 바
        hp_ratio = self.player_hp / self.player_max_hp
        bar_w = 200
        bar_h = 20
        bar_x = 20
        bar_y = SCREEN_H - 40
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(self.screen, DARK_RED, (bar_x, bar_y, bar_w, bar_h))
        if hp_ratio > 0:
            color = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        hp_text = self.font.render(f"HP: {int(self.player_hp)}", True, WHITE)
        self.screen.blit(hp_text, (bar_x + bar_w + 10, bar_y))

        # 탄약
        ammo_text = self.font.render(
            f"AMMO: {self.weapon.ammo}/{self.weapon.mag_size}  RESERVE: {self.weapon.reserve_ammo}",
            True, WHITE)
        self.screen.blit(ammo_text, (SCREEN_W - 350, SCREEN_H - 40))

        # 점수/킬
        score_text = self.font.render(f"SCORE: {self.score}  KILLS: {self.kills}", True, YELLOW)
        self.screen.blit(score_text, (20, 20))

        # 웨이브
        wave_text = self.font.render(f"WAVE: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (20, 50))

        # 남은 적
        alive = sum(1 for e in self.enemies if e.state != "dead")
        enemy_text = self.font.render(f"ENEMIES: {alive}", True, RED)
        self.screen.blit(enemy_text, (20, 80))

        # 재장전 표시
        if self.weapon.is_reloading:
            reload_text = self.big_font.render("RELOADING...", True, YELLOW)
            text_rect = reload_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60))
            self.screen.blit(reload_text, text_rect)

        # 웨이브 전환
        if self.wave_transition > 0:
            wave_announce = self.big_font.render(f"WAVE {self.wave}", True, YELLOW)
            text_rect = wave_announce.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3))
            self.screen.blit(wave_announce, text_rect)

        # 크로스헤어
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        spread = 8 + int(self.weapon.spread * 500)
        pygame.draw.line(self.screen, WHITE, (cx - spread - 5, cy), (cx - spread + 5, cy), 2)
        pygame.draw.line(self.screen, WHITE, (cx + spread - 5, cy), (cx + spread + 5, cy), 2)
        pygame.draw.line(self.screen, WHITE, (cx, cy - spread - 5), (cx, cy - spread + 5), 2)
        pygame.draw.line(self.screen, WHITE, (cx, cy + spread - 5), (cx, cy + spread + 5), 2)
        pygame.draw.circle(self.screen, WHITE, (cx, cy), 2)

        # 데미지 플래시
        if self.damage_flash > 0:
            alpha = int(self.damage_flash * 100)
            flash_surf = pygame.Surface((SCREEN_W, SCREEN_H))
            flash_surf.fill(RED)
            flash_surf.set_alpha(alpha)
            self.screen.blit(flash_surf, (0, 0))

        # 미니맵
        self.render_minimap()

    def render_minimap(self):
        """미니맵"""
        map_scale = 4
        mm_w = MAP_W * map_scale
        mm_h = MAP_H * map_scale
        mm_x = SCREEN_W - mm_w - 10
        mm_y = 10

        pygame.draw.rect(self.screen, (0, 0, 0, 180), (mm_x - 2, mm_y - 2, mm_w + 4, mm_h + 4))

        for my in range(MAP_H):
            for mx in range(MAP_W):
                if MAP[my][mx] != 0:
                    color = GRAY if MAP[my][mx] == 1 else BROWN
                    pygame.draw.rect(self.screen, color,
                                   (mm_x + mx * map_scale, mm_y + my * map_scale,
                                    map_scale, map_scale))

        # 플레이어
        px_mm = mm_x + int(self.px * map_scale)
        py_mm = mm_y + int(self.py * map_scale)
        pygame.draw.circle(self.screen, GREEN, (px_mm, py_mm), 3)
        # 시야 방향
        pygame.draw.line(self.screen, GREEN,
                        (px_mm, py_mm),
                        (px_mm + int(math.cos(self.pa) * 8),
                         py_mm + int(math.sin(self.pa) * 8)), 2)

        # 적
        for enemy in self.enemies:
            if enemy.state != "dead":
                ex_mm = mm_x + int(enemy.x * map_scale)
                ey_mm = mm_y + int(enemy.y * map_scale)
                pygame.draw.circle(self.screen, RED, (ex_mm, ey_mm), 2)

    def render_game_over(self):
        """게임 오버 화면"""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        go_text = self.big_font.render("GAME OVER", True, RED)
        text_rect = go_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 40))
        self.screen.blit(go_text, text_rect)

        score_text = self.font.render(f"Final Score: {self.score}  Kills: {self.kills}  Wave: {self.wave}",
                                     True, WHITE)
        text_rect = score_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20))
        self.screen.blit(score_text, text_rect)

        restart_text = self.font.render("Press R to restart", True, YELLOW)
        text_rect = restart_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 60))
        self.screen.blit(restart_text, text_rect)

    def shoot(self):
        """발사"""
        w = self.weapon
        if w.is_reloading or w.fire_cooldown > 0:
            return
        if w.ammo <= 0:
            self.reload()
            return

        w.ammo -= 1
        w.fire_cooldown = w.fire_rate
        w.muzzle_flash = 0.05
        w.recoil = min(w.recoil + 0.005, 0.05)
        self.sounds['shoot'].play()

        # 탄 퍼짐
        spread = w.spread + w.recoil
        angle = self.pa + random.uniform(-spread, spread)

        # 히트스캔
        dx = math.cos(angle)
        dy = math.sin(angle)

        # 벽까지의 거리
        wall_dist, _, _, _ = self.cast_ray(angle)

        # 적 명중 체크
        closest_hit = None
        closest_dist = wall_dist

        for enemy in self.enemies:
            if enemy.state == "dead":
                continue
            # 적과 레이의 교차 체크
            ex = enemy.x - self.px
            ey = enemy.y - self.py

            # 레이 방향으로의 투영
            proj = ex * dx + ey * dy
            if proj < 0 or proj > closest_dist:
                continue

            # 수직 거리
            perp_dist = abs(ex * dy - ey * dx)
            if perp_dist < 0.3: # 적 반경
                closest_hit = enemy
                closest_dist = proj

        if closest_hit:
            closest_hit.hp -= w.damage
            closest_hit.hit_flash = 0.1
            self.sounds['hit'].play()
            # 피 파티클
            for _ in range(5):
                self.particles.append(Particle(
                    x=closest_hit.x, y=closest_hit.y,
                    dx=random.uniform(-2, 2), dy=random.uniform(-2, 2),
                    life=0.3, max_life=0.3, color=RED, size=3
                ))
            if closest_hit.hp <= 0:
                closest_hit.state = "dead"
                closest_hit.death_timer = 0.5
                self.kills += 1
                self.score += 100
                self.sounds['enemy_die'].play()
                # 사망 파티클
                for _ in range(15):
                    self.particles.append(Particle(
                        x=closest_hit.x, y=closest_hit.y,
                        dx=random.uniform(-3, 3), dy=random.uniform(-3, 3),
                        life=0.5, max_life=0.5, color=DARK_RED, size=4
                    ))

    def reload(self):
        """재장전"""
        w = self.weapon
        if w.is_reloading or w.ammo == w.mag_size or w.reserve_ammo <= 0:
            return
        w.is_reloading = True
        w.reload_timer = w.reload_time
        self.sounds['reload'].play()

    def update_weapon(self, dt):
        """무기 상태 업데이트"""
        w = self.weapon
        w.fire_cooldown = max(0, w.fire_cooldown - dt)
        w.muzzle_flash = max(0, w.muzzle_flash - dt)
        w.recoil = max(0.01, w.recoil - dt * 0.05)

        if w.is_reloading:
            w.reload_timer -= dt
            if w.reload_timer <= 0:
                needed = w.mag_size - w.ammo
                take = min(needed, w.reserve_ammo)
                w.ammo += take
                w.reserve_ammo -= take
                w.is_reloading = False

    def update_enemies(self, dt):
        """적 AI 업데이트"""
        for enemy in self.enemies:
            if enemy.state == "dead":
                enemy.death_timer -= dt
                continue

            enemy.hit_flash = max(0, enemy.hit_flash - dt)
            enemy.attack_cooldown = max(0, enemy.attack_cooldown - dt)

            dx = self.px - enemy.x
            dy = self.py - enemy.y
            dist = math.hypot(dx, dy)

            # 시야 체크 (벽에 가려져 있는지)
            has_los = True
            if dist > 0.1:
                steps = int(dist * 4)
                for i in range(1, steps):
                    t = i / steps
                    check_x = enemy.x + dx * t
                    check_y = enemy.y + dy * t
                    if is_wall(check_x, check_y):
                        has_los = False
                        break

            # 상태 전이
            if dist < enemy.alert_radius and has_los:
                enemy.state = "chase"
                enemy.last_seen_x = self.px
                enemy.last_seen_y = self.py
            elif enemy.state == "chase" and (dist > enemy.alert_radius * 1.5 or not has_los):
                enemy.state = "idle"

            # 행동
            if enemy.state == "chase":
                if dist > enemy.attack_range * 0.7:
                    # 추적
                    move_angle = math.atan2(dy, dx)
                    new_x = enemy.x + math.cos(move_angle) * enemy.speed * dt
                    new_y = enemy.y + math.sin(move_angle) * enemy.speed * dt
                    if not is_wall(new_x, enemy.y):
                        enemy.x = new_x
                    if not is_wall(enemy.x, new_y):
                        enemy.y = new_y
                else:
                    # 공격
                    if enemy.attack_cooldown <= 0:
                        enemy.attack_cooldown = 1.0
                        # 명중 체크 (거리 기반 확률)
                        hit_chance = max(0.3, 1.0 - dist / enemy.attack_range)
                        if random.random() < hit_chance:
                            self.player_hp -= enemy.damage
                            self.damage_flash = 0.5
                            self.sounds['hit'].play()
            else:
                # 순찰
                enemy.patrol_timer -= dt
                if enemy.patrol_timer <= 0:
                    enemy.patrol_timer = random.uniform(2, 5)
                    enemy.patrol_angle = random.uniform(0, 2 * math.pi)
                new_x = enemy.x + math.cos(enemy.patrol_angle) * enemy.speed * 0.3 * dt
                new_y = enemy.y + math.sin(enemy.patrol_angle) * enemy.speed * 0.3 * dt
                if not is_wall(new_x, enemy.y):
                    enemy.x = new_x
                if not is_wall(enemy.x, new_y):
                    enemy.y = new_y

        # 완전히 사망한 적 제거
        self.enemies = [e for e in self.enemies if not (e.state == "dead" and e.death_timer <= 0)]

    def update_particles(self, dt):
        """파티클 업데이트"""
        for p in self.particles:
            p.x += p.dx * dt
            p.y += p.dy * dt
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def update(self, dt):
        """메인 업데이트"""
        if self.game_over:
            self.game_over_timer += dt
            return

        # 웨이브 전환 타이머
        if self.wave_transition > 0:
            self.wave_transition -= dt

        # 다음 웨이브 체크
        alive_enemies = sum(1 for e in self.enemies if e.state != "dead")
        if alive_enemies == 0 and self.wave_transition <= 0:
            self.spawn_wave()

        # 플레이어 이동
        keys = pygame.key.get_pressed()
        speed = self.sprint_speed if keys[pygame.K_LSHIFT] else self.player_speed

        move_x = 0
        move_y = 0
        if keys[pygame.K_w]:
            move_x += math.cos(self.pa)
            move_y += math.sin(self.pa)
        if keys[pygame.K_s]:
            move_x -= math.cos(self.pa)
            move_y -= math.sin(self.pa)
        if keys[pygame.K_a]:
            move_x += math.cos(self.pa - math.pi / 2)
            move_y += math.sin(self.pa - math.pi / 2)
        if keys[pygame.K_d]:
            move_x += math.cos(self.pa + math.pi / 2)
            move_y += math.sin(self.pa + math.pi / 2)

        # 정규화
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            move_x = move_x / move_len * speed * dt
            move_y = move_y / move_len * speed * dt

            # 충돌 체크
            new_px = self.px + move_x
            new_py = self.py + move_y

            if not is_wall(new_px + math.copysign(self.player_radius, move_x), self.py):
                self.px = new_px
            if not is_wall(self.px, new_py + math.copysign(self.player_radius, move_y)):
                self.py = new_py

            # 헤드밥
            self.bob_phase += dt * 10
            self.bob_amount = math.sin(self.bob_phase) * 0.5 + 0.5

            # 발소리
            self.step_timer -= dt
            if self.step_timer <= 0:
                self.step_timer = 0.4 if speed < 5 else 0.25
                self.sounds['step'].play()
        else:
            self.bob_amount *= 0.9

        # 마우스 회전
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        self.pa += mouse_dx * self.mouse_sensitivity

        # 업데이트
        self.update_weapon(dt)
        self.update_enemies(dt)
        self.update_particles(dt)

        # 데미지 플래시 감소
        self.damage_flash = max(0, self.damage_flash - dt * 2)

        # 게임 오버 체크
        if self.player_hp <= 0:
            self.player_hp = 0
            self.game_over = True
            self.game_over_timer = 0

    def render(self):
        """렌더링"""
        self.render_floor_ceiling()
        z_buffer = self.render_walls()
        self.render_enemies(z_buffer)
        self.render_weapon()
        self.render_hud()

        if self.game_over:
            self.render_game_over()

    def reset(self):
        """게임 리셋"""
        self.px = 12.0
        self.py = 10.0
        self.pa = 0.0
        self.player_hp = self.player_max_hp
        self.weapon = Weapon()
        self.bullets.clear()
        self.enemies.clear()
        self.particles.clear()
        self.score = 0
        self.kills = 0
        self.wave = 0
        self.game_over = False
        self.game_over_timer = 0.0
        self.wave_transition = 0.0
        self.damage_flash = 0.0
        self.spawn_wave()

    def run(self):
        """메인 루프"""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05) # 프레임 시간 제한

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        if self.game_over:
                            self.reset()
                        else:
                            self.reload()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not self.game_over:
                        self.shoot()

            if not self.game_over:
                self.update(dt)
            else:
                # 게임 오버 후 R키 대기
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r] and self.game_over_timer > 1.0:
                    self.reset()

            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ─────────────────────────────────────────────
# 시작
# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
