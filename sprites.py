"""
精灵模块
包含所有游戏角色的类定义：坦克、子弹、墙壁、爆炸效果、道具
"""
import pygame
import random
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TANK_SIZE,
    PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED,
    WHITE, BLACK, RED, GREEN, BLUE, YELLOW,
    GRAY, DARK_GRAY, BROWN, PLAYER_LIVES, INVINCIBLE_TIME
)


class BrickWall(pygame.sprite.Sprite):
    """砖墙 - 可被摧毁"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TANK_SIZE, TANK_SIZE))
        self.image.fill(BROWN)
        # 画砖纹
        for row in range(4):
            for col in range(4):
                offset = 5 if row % 2 == 0 else 0
                pygame.draw.rect(self.image, (160, 82, 45),
                               (col * 10 + offset, row * 10, 9, 9))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.health = 3

    def hit(self):
        """被子弹击中"""
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        # 显示损坏效果
        damage_level = 3 - self.health
        if damage_level == 1:
            pygame.draw.line(self.image, DARK_GRAY, (5, 5), (35, 35), 3)
            pygame.draw.line(self.image, DARK_GRAY, (35, 5), (5, 35), 3)
        elif damage_level == 2:
            pygame.draw.line(self.image, DARK_GRAY, (0, 0), (40, 40), 3)
            pygame.draw.line(self.image, DARK_GRAY, (40, 0), (0, 40), 3)
            pygame.draw.line(self.image, DARK_GRAY, (20, 0), (20, 40), 3)
            pygame.draw.line(self.image, DARK_GRAY, (0, 20), (40, 20), 3)
        return False


class SteelWall(pygame.sprite.Sprite):
    """钢铁墙 - 默认不可摧毁，强化子弹可摧毁"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TANK_SIZE, TANK_SIZE))
        self.image.fill(GRAY)
        pygame.draw.rect(self.image, WHITE, (0, 0, TANK_SIZE, TANK_SIZE), 2)
        pygame.draw.rect(self.image, DARK_GRAY, (5, 5, 30, 30))
        pygame.draw.circle(self.image, WHITE, (20, 20), 8, 2)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.health = 1  # 需要强化子弹才能击毁
        self.steel = True

    def hit(self):
        """被强化子弹击中"""
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        return False


class Water(pygame.sprite.Sprite):
    """水 - 坦克不能进入，子弹可以穿过"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TANK_SIZE, TANK_SIZE))
        self.image.fill((0, 100, 180))  # 深蓝色水底
        # 水波纹
        for i in range(0, TANK_SIZE, 8):
            offset = (i // 8) % 2
            for j in range(offset, TANK_SIZE, 16):
                pygame.draw.ellipse(self.image, (50, 150, 220),
                                   (j, i, 12, 6))
                pygame.draw.ellipse(self.image, (100, 200, 255),
                                   (j + 2, i + 2, 8, 2))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Explosion(pygame.sprite.Sprite):
    """爆炸效果"""
    def __init__(self, x, y, size=TANK_SIZE):
        super().__init__()
        self.size = size
        self.frame = 0
        self.max_frame = 10
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.update()

    def update(self):
        self.frame += 1
        if self.frame >= self.max_frame:
            self.kill()
            return

        self.image.fill((0, 0, 0, 0))
        progress = self.frame / self.max_frame
        radius = int(self.size // 2 * (0.3 + progress * 0.7))
        alpha = int(255 * (1 - progress))

        color_ratio = self.frame / self.max_frame
        r = 255
        g = int(255 * (1 - color_ratio))
        b = 0

        pygame.draw.circle(self.image, (r, g, b, alpha),
                         (self.size // 2, self.size // 2), radius)
        pygame.draw.circle(self.image, (255, 255, 200, alpha),
                         (self.size // 2, self.size // 2), radius // 2)


class Base(pygame.sprite.Sprite):
    """老窝 - 被摧毁则游戏结束"""
    def __init__(self, x, y):
        super().__init__()
        self.size = TANK_SIZE
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.alive = True
        self._draw_base()

    def _draw_base(self):
        """绘制旗帜/鹰标"""
        self.image.fill((0, 0, 0, 0))
        cx, cy = self.size // 2, self.size // 2

        # 底座
        pygame.draw.rect(self.image, (100, 100, 100), (cx - 12, cy + 6, 24, 10))
        pygame.draw.rect(self.image, (150, 150, 150), (cx - 10, cy + 7, 20, 6))

        # 旗杆
        pygame.draw.rect(self.image, (180, 180, 180), (cx - 1, cy - 12, 3, 20))

        # 旗帜（三角形）
        flag_points = [(cx + 2, cy - 12), (cx + 16, cy - 7), (cx + 2, cy - 2)]
        pygame.draw.polygon(self.image, (255, 200, 0), flag_points)

        # 星星在旗帜上
        pygame.draw.circle(self.image, (255, 255, 0), (cx + 7, cy - 7), 2)

    def kill(self):
        """老窝被摧毁"""
        self.alive = False
        self.image.fill((0, 0, 0, 0))
        cx, cy = self.size // 2, self.size // 2
        pygame.draw.line(self.image, (255, 0, 0), (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
        pygame.draw.line(self.image, (255, 0, 0), (cx + 10, cy - 10), (cx - 10, cy + 10), 3)
        pygame.draw.rect(self.image, (100, 50, 50), (cx - 12, cy + 6, 24, 10))
        super().kill()


class Bullet(pygame.sprite.Sprite):
    """子弹"""
    def __init__(self, x, y, direction, speed=BULLET_SPEED, enemy=False, powered=False):
        super().__init__()
        size = 12 if powered else 8
        self.image = pygame.Surface((size, size))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed * 2 if powered else speed
        self.direction = direction
        self.enemy = enemy
        self.powered = powered

        # 子弹外观
        if enemy:
            self.image.fill(RED)
            pygame.draw.circle(self.image, YELLOW, (size // 2, size // 2), 3)
        else:
            if powered:
                self.image.fill((255, 200, 0))  # 亮金色
                pygame.draw.circle(self.image, WHITE, (size // 2, size // 2), 4)
            else:
                self.image.fill(YELLOW)
                pygame.draw.circle(self.image, WHITE, (size // 2, size // 2), 3)

    def update(self):
        """更新子弹位置"""
        if self.direction == "up":
            self.rect.y -= self.speed
        elif self.direction == "down":
            self.rect.y += self.speed
        elif self.direction == "left":
            self.rect.x -= self.speed
        elif self.direction == "right":
            self.rect.x += self.speed

        # 超出窗口则销毁
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    """道具 - 击杀敌人后概率掉落"""
    TYPES = ["freeze", "life", "bomb", "gun", "boat", "star", "helmet", "shovel"]

    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice(self.TYPES)
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.blink_timer = 0
        self._draw_icon()

    def _draw_icon(self):
        """根据道具类型绘制图标"""
        self.image.fill((0, 0, 0, 0))

        # 背景闪烁圆
        pygame.draw.circle(self.image, (255, 255, 255, 200),
                          (self.size // 2, self.size // 2), self.size // 2)
        pygame.draw.circle(self.image, (0, 0, 0, 200),
                          (self.size // 2, self.size // 2), self.size // 2 - 2)

        if self.type == "freeze":
            # 雪花图标 - 蓝色
            color = (100, 200, 255)
            cx, cy = self.size // 2, self.size // 2
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                ex = cx + int(10 * math.cos(rad))
                ey = cy + int(10 * math.sin(rad))
                pygame.draw.line(self.image, color, (cx, cy), (ex, ey), 2)
            pygame.draw.circle(self.image, color, (cx, cy), 4)

        elif self.type == "life":
            # 加命图标 - 绿色 + 号
            color = (100, 255, 100)
            cx, cy = self.size // 2, self.size // 2
            pygame.draw.rect(self.image, color, (cx - 4, cy - 8, 8, 16))
            pygame.draw.rect(self.image, color, (cx - 8, cy - 4, 16, 8))
            # 外框
            pygame.draw.rect(self.image, (200, 255, 200),
                            (cx - 8, cy - 8, 16, 16), 1)

        elif self.type == "bomb":
            # 炸弹图标 - 红色骷髅/炸弹
            color = (255, 100, 100)
            cx, cy = self.size // 2, self.size // 2
            # 炸弹圆
            pygame.draw.circle(self.image, color, (cx, cy), 8)
            # 引信
            pygame.draw.line(self.image, (200, 200, 100),
                            (cx + 5, cy - 2), (cx + 10, cy - 8), 2)
            pygame.draw.circle(self.image, (255, 200, 0),
                              (cx + 10, cy - 8), 2)

        elif self.type == "gun":
            # 手枪图标 - 金色
            color = (255, 215, 0)
            cx, cy = self.size // 2, self.size // 2
            # 枪管
            pygame.draw.rect(self.image, color, (cx + 2, cy - 3, 12, 6))
            # 枪身
            pygame.draw.rect(self.image, (200, 170, 0), (cx - 6, cy - 5, 10, 10))
            # 扳机
            pygame.draw.rect(self.image, (150, 120, 0), (cx - 3, cy + 5, 4, 4))

        elif self.type == "boat":
            # 船图标 - 蓝色波浪上的船
            cx, cy = self.size // 2, self.size // 2
            # 船身
            boat_pts = [(cx - 10, cy + 2), (cx + 10, cy + 2), (cx + 6, cy - 4), (cx - 6, cy - 4)]
            pygame.draw.polygon(self.image, (139, 69, 19), boat_pts)
            # 桅杆
            pygame.draw.line(self.image, (100, 100, 100), (cx, cy - 4), (cx, cy - 10), 2)
            # 帆
            sail_pts = [(cx + 1, cy - 10), (cx + 8, cy - 6), (cx + 1, cy - 3)]
            pygame.draw.polygon(self.image, (255, 255, 255), sail_pts)
            # 水波纹
            pygame.draw.ellipse(self.image, (50, 150, 220), (cx - 12, cy + 4, 24, 5))

        elif self.type == "star":
            # 星星图标 - 金色五角星（坦克升级）
            color = (255, 215, 0)
            cx, cy = self.size // 2, self.size // 2
            outer_r = 12
            inner_r = 5
            points = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                r = outer_r if i % 2 == 0 else inner_r
                points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
            pygame.draw.polygon(self.image, color, points)
            pygame.draw.polygon(self.image, (255, 255, 200), points, 1)

        elif self.type == "helmet":
            # 头盔图标 - 银色半圆护盾
            cx, cy = self.size // 2, self.size // 2
            # 半圆形头盔
            helmet_rect = pygame.Rect(cx - 12, cy - 8, 24, 18)
            pygame.draw.ellipse(self.image, (180, 180, 190), helmet_rect)
            pygame.draw.ellipse(self.image, (220, 220, 230), (cx - 10, cy - 6, 20, 12))
            # 护目镜横条
            pygame.draw.rect(self.image, (80, 80, 90), (cx - 10, cy + 1, 20, 4))
            pygame.draw.rect(self.image, (150, 150, 160), (cx - 8, cy + 2, 16, 2))

        elif self.type == "shovel":
            # 铲子图标 - 棕色铲形
            cx, cy = self.size // 2, self.size // 2
            # 铲柄
            pygame.draw.rect(self.image, (139, 90, 43), (cx - 1, cy - 12, 3, 18))
            # 铲头（梯形）
            shovel_pts = [(cx - 8, cy + 6), (cx + 8, cy + 6),
                          (cx + 4, cy + 2), (cx - 4, cy + 2)]
            pygame.draw.polygon(self.image, (160, 110, 50), shovel_pts)
            pygame.draw.polygon(self.image, (180, 130, 60), shovel_pts, 1)
            # 铲刃
            pygame.draw.line(self.image, (200, 200, 200), (cx - 7, cy + 6), (cx + 7, cy + 6), 1)

    def update(self):
        """闪烁效果"""
        self.blink_timer += 1

    def apply(self, game_manager):
        """应用道具效果"""
        if self.type == "freeze":
            game_manager.freeze_enemies()
        elif self.type == "life":
            game_manager.add_life()
        elif self.type == "bomb":
            game_manager.bomb_all_enemies()
        elif self.type == "gun":
            game_manager.enable_gun()
        elif self.type == "boat":
            game_manager.enable_boat()
        elif self.type == "star":
            game_manager.upgrade_tank()
        elif self.type == "helmet":
            game_manager.enable_helmet()
        elif self.type == "shovel":
            game_manager.enable_shovel()

    def draw_with_glow(self, screen):
        """绘制带闪烁效果的道具"""
        alpha = 128 + int(127 * math.sin(self.blink_timer * 0.1))
        glow = pygame.Surface((self.size + 10, self.size + 10), pygame.SRCALPHA)
        color = (255, 255, 255, alpha // 4)
        pygame.draw.circle(glow, color,
                          ((self.size + 10) // 2, (self.size + 10) // 2),
                          (self.size + 10) // 2)
        screen.blit(glow, (self.rect.x - 5, self.rect.y - 5))
        screen.blit(self.image, self.rect)


class Tank(pygame.sprite.Sprite):
    """坦克基类（玩家和敌人共用）"""

    # 敌人类型属性映射
    ENEMY_SPEEDS = {'basic': 2, 'fast': 4, 'armored': 2, 'power': 2}
    ENEMY_HP = {'basic': 1, 'fast': 1, 'armored': 4, 'power': 1}
    ENEMY_SCORES = {'basic': 100, 'fast': 200, 'armored': 300, 'power': 400}

    def __init__(self, x, y, color, speed=PLAYER_SPEED, enemy=False, enemy_type='basic'):
        super().__init__()
        self.width = TANK_SIZE
        self.height = TANK_SIZE
        self.color = color
        self.enemy = enemy
        self.enemy_type = enemy_type if enemy else None

        # 敌方速度由类型决定，玩家速度由参数决定
        if enemy:
            self.speed = self.ENEMY_SPEEDS.get(enemy_type, 2)
        else:
            self.speed = speed

        self.direction = "up"
        self.shoot_cooldown = 0
        self.max_cooldown = 15
        self.lives = PLAYER_LIVES if not enemy else 1

        # 敌方 HP（装甲坦克可承受多次攻击）
        if enemy:
            self.hp = self.ENEMY_HP.get(enemy_type, 1)
            self.max_hp = self.hp
        else:
            self.hp = 1
            self.max_hp = 1

        self.upgrade_level = 0  # 玩家升级等级 0-3

        self.image = pygame.Surface((self.width, self.height))
        self.original_color = color
        self.update_image()

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.invincible_time = 0
        self.blink_timer = 0
        self.frozen_time = 0  # 被冰冻剩余时间
        self.boat_mode = False  # 船道具：可进入水面
        self.spawning = True if enemy else False  # 敌方出生动画
        self.spawn_timer = 90 if enemy else 0  # 1.5秒 (60fps)

    def _draw_player_tank(self):
        """绘制玩家黄色坦克（仿经典坦克大战风格）"""
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BLACK)

        # === 履带（两侧深色履带 + 履带纹路） ===
        track_dark = (50, 50, 50)       # 履带底色
        track_light = (110, 110, 110)   # 履带凸起纹
        # 左履带
        pygame.draw.rect(self.image, track_dark, (0, 2, 9, 36))
        for i in range(0, 36, 5):
            pygame.draw.rect(self.image, track_light, (1, 3 + i, 7, 2))
        # 右履带
        pygame.draw.rect(self.image, track_dark, (31, 2, 9, 36))
        for i in range(0, 36, 5):
            pygame.draw.rect(self.image, track_light, (32, 3 + i, 7, 2))

        # === 车身主体 ===
        body_dark = (180, 160, 0)       # 车身暗面（边缘）
        body_main = (230, 210, 0)       # 车身主色
        body_light = (255, 240, 100)    # 车身亮面（高光）

        # 车身主体矩形（左履带右边 到 右履带左边）
        body_rect = pygame.Rect(9, 4, 22, 32)
        pygame.draw.rect(self.image, body_main, body_rect)

        # 车身顶部高光条
        pygame.draw.rect(self.image, body_light, (10, 5, 20, 4))

        # 车身底部暗边
        pygame.draw.rect(self.image, body_dark, (9, 33, 22, 3))

        # 车身左右边缘暗线
        pygame.draw.line(self.image, body_dark, (9, 5), (9, 35), 1)
        pygame.draw.line(self.image, body_dark, (30, 5), (30, 35), 1)

        # 车身中间分界线（模拟两块装甲板拼接）
        pygame.draw.line(self.image, body_dark, (20, 8), (20, 30), 1)

        # === 炮塔（半圆形穹顶） ===
        turret_dark = (170, 150, 0)
        turret_main = (240, 220, 50)
        turret_light = (255, 250, 180)

        # 炮塔底座圆
        pygame.draw.circle(self.image, turret_dark, (20, 20), 11)
        pygame.draw.circle(self.image, turret_main, (20, 20), 9)
        # 炮塔高光（左上小弧）
        pygame.draw.circle(self.image, turret_light, (18, 18), 4)

        # === 炮管 ===
        barrel_dark = (100, 100, 100)   # 炮管暗面
        barrel_main = (160, 160, 160)   # 炮管主色
        barrel_light = (210, 210, 210)  # 炮管高光

        if self.direction == "up":
            # 炮管座（连接炮塔的部分）
            pygame.draw.rect(self.image, barrel_dark, (16, 5, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (17, 5, 6, 7))
            # 炮管主体
            pygame.draw.rect(self.image, barrel_main, (17, 0, 6, 7))
            pygame.draw.rect(self.image, barrel_light, (18, 0, 2, 6))
            # 炮口
            pygame.draw.rect(self.image, barrel_dark, (17, 0, 6, 2))

        elif self.direction == "down":
            pygame.draw.rect(self.image, barrel_dark, (16, 27, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (17, 28, 6, 7))
            pygame.draw.rect(self.image, barrel_main, (17, 33, 6, 7))
            pygame.draw.rect(self.image, barrel_light, (18, 34, 2, 6))
            pygame.draw.rect(self.image, barrel_dark, (17, 38, 6, 2))

        elif self.direction == "left":
            pygame.draw.rect(self.image, barrel_dark, (5, 16, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (5, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_main, (0, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_light, (0, 18, 6, 2))
            pygame.draw.rect(self.image, barrel_dark, (0, 17, 2, 6))

        elif self.direction == "right":
            pygame.draw.rect(self.image, barrel_dark, (27, 16, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (28, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_main, (33, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_light, (34, 18, 6, 2))
            pygame.draw.rect(self.image, barrel_dark, (38, 17, 2, 6))

        # === 升级等级外观增强 ===
        gold = (255, 215, 0)
        if self.upgrade_level >= 1:
            # 等级1+：炮管延长
            extra = 2 if self.upgrade_level == 1 else 4
            if self.direction == "up":
                pygame.draw.rect(self.image, barrel_main, (17, -extra, 6, extra + 2))
                pygame.draw.rect(self.image, barrel_light, (18, -extra, 2, extra + 1))
            elif self.direction == "down":
                pygame.draw.rect(self.image, barrel_main, (17, 38, 6, extra + 2))
                pygame.draw.rect(self.image, barrel_light, (18, 39, 2, extra + 1))
            elif self.direction == "left":
                pygame.draw.rect(self.image, barrel_main, (-extra, 17, extra + 2, 6))
                pygame.draw.rect(self.image, barrel_light, (-extra, 18, extra + 1, 2))
            elif self.direction == "right":
                pygame.draw.rect(self.image, barrel_main, (38, 17, extra + 2, 6))
                pygame.draw.rect(self.image, barrel_light, (38, 18, extra + 1, 2))

        if self.upgrade_level >= 2:
            # 等级2+：车身两侧金色竖条
            pygame.draw.rect(self.image, gold, (12, 6, 2, 28))
            pygame.draw.rect(self.image, gold, (26, 6, 2, 28))

        if self.upgrade_level >= 3:
            # 等级3：车身金色高亮边框
            pygame.draw.rect(self.image, gold, (9, 4, 22, 32), 1)
            # 炮塔金色光环
            pygame.draw.circle(self.image, gold, (20, 20), 12, 1)

    def _draw_enemy_tank(self):
        """绘制敌方坦克（根据类型使用不同配色）"""
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BLACK)

        # 根据类型选择配色方案 (暗面, 主色, 亮面)
        if self.enemy_type == 'basic':
            body_dark, body_main, body_light = (140, 20, 20), (200, 50, 50), (240, 120, 120)
            turret_dark, turret_main, turret_light = (140, 20, 20), (220, 80, 80), (255, 160, 160)
        elif self.enemy_type == 'fast':
            body_dark, body_main, body_light = (150, 60, 10), (220, 100, 30), (250, 160, 80)
            turret_dark, turret_main, turret_light = (150, 60, 10), (240, 130, 50), (255, 190, 110)
        elif self.enemy_type == 'armored':
            # 银灰色调，随受损变暗
            darken = int(80 * (1 - self.hp / max(self.max_hp, 1)))
            body_dark = (100 - darken, 105 - darken, 115 - darken)
            body_main = (160 - darken, 165 - darken, 175 - darken)
            body_light = (200 - darken, 205 - darken, 215 - darken)
            turret_dark = (110 - darken, 115 - darken, 125 - darken)
            turret_main = (180 - darken, 185 - darken, 195 - darken)
            turret_light = (220 - darken, 225 - darken, 235 - darken)
        elif self.enemy_type == 'power':
            body_dark, body_main, body_light = (160, 20, 10), (240, 50, 40), (255, 120, 100)
            turret_dark, turret_main, turret_light = (160, 20, 10), (255, 70, 50), (255, 150, 130)
        else:
            body_dark, body_main, body_light = (140, 20, 20), (200, 50, 50), (240, 120, 120)
            turret_dark, turret_main, turret_light = (140, 20, 20), (220, 80, 80), (255, 160, 160)

        # === 履带 ===
        track_dark = (50, 50, 50)
        track_light = (110, 110, 110)
        # 左履带
        pygame.draw.rect(self.image, track_dark, (0, 2, 9, 36))
        for i in range(0, 36, 5):
            pygame.draw.rect(self.image, track_light, (1, 3 + i, 7, 2))
        # 右履带
        pygame.draw.rect(self.image, track_dark, (31, 2, 9, 36))
        for i in range(0, 36, 5):
            pygame.draw.rect(self.image, track_light, (32, 3 + i, 7, 2))

        # === 车身主体 ===
        body_rect = pygame.Rect(9, 4, 22, 32)
        pygame.draw.rect(self.image, body_main, body_rect)
        pygame.draw.rect(self.image, body_light, (10, 5, 20, 4))
        pygame.draw.rect(self.image, body_dark, (9, 33, 22, 3))
        pygame.draw.line(self.image, body_dark, (9, 5), (9, 35), 1)
        pygame.draw.line(self.image, body_dark, (30, 5), (30, 35), 1)
        pygame.draw.line(self.image, body_dark, (20, 8), (20, 30), 1)

        # === 炮塔 ===
        pygame.draw.circle(self.image, turret_dark, (20, 20), 11)
        pygame.draw.circle(self.image, turret_main, (20, 20), 9)
        pygame.draw.circle(self.image, turret_light, (18, 18), 4)

        # === 炮管 ===
        barrel_dark = (100, 100, 100)
        barrel_main = (160, 160, 160)
        barrel_light = (210, 210, 210)

        if self.direction == "up":
            pygame.draw.rect(self.image, barrel_dark, (16, 5, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (17, 5, 6, 7))
            pygame.draw.rect(self.image, barrel_main, (17, 0, 6, 7))
            pygame.draw.rect(self.image, barrel_light, (18, 0, 2, 6))
            pygame.draw.rect(self.image, barrel_dark, (17, 0, 6, 2))
        elif self.direction == "down":
            pygame.draw.rect(self.image, barrel_dark, (16, 27, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (17, 28, 6, 7))
            pygame.draw.rect(self.image, barrel_main, (17, 33, 6, 7))
            pygame.draw.rect(self.image, barrel_light, (18, 34, 2, 6))
            pygame.draw.rect(self.image, barrel_dark, (17, 38, 6, 2))
        elif self.direction == "left":
            pygame.draw.rect(self.image, barrel_dark, (5, 16, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (5, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_main, (0, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_light, (0, 18, 6, 2))
            pygame.draw.rect(self.image, barrel_dark, (0, 17, 2, 6))
        elif self.direction == "right":
            pygame.draw.rect(self.image, barrel_dark, (27, 16, 8, 8))
            pygame.draw.rect(self.image, barrel_main, (28, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_main, (33, 17, 7, 6))
            pygame.draw.rect(self.image, barrel_light, (34, 18, 6, 2))
            pygame.draw.rect(self.image, barrel_dark, (38, 17, 2, 6))

        # 装甲坦克损伤叠加暗色
        if self.enemy_type == 'armored' and self.hp < self.max_hp:
            darken_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(60 * (1 - self.hp / self.max_hp))
            darken_surf.fill((0, 0, 0, alpha))
            self.image.blit(darken_surf, (0, 0))

    def update_image(self):
        """更新坦克图像，包括炮管方向"""
        if self.enemy:
            self._draw_enemy_tank()
        else:
            self._draw_player_tank()

    def update(self, keys=None, walls=None, tanks=None, player=None):
        """更新状态"""
        # 出生动画（敌方专用）
        if self.spawning:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.spawning = False
                self.image.set_alpha(255)
            else:
                # 每6帧切换可见/不可见
                self.image.set_alpha(0 if (self.spawn_timer // 6) % 2 == 0 else 255)
            return  # 出生期间不执行任何操作

        # 无敌闪烁
        if self.invincible_time > 0:
            self.invincible_time -= 1
            self.blink_timer += 1
            self.image.set_alpha(128 if self.blink_timer % 6 < 3 else 255)
        else:
            self.image.set_alpha(255)

        # 冰冻效果
        if self.frozen_time > 0:
            self.frozen_time -= 1
            # 冰冻时闪烁蓝色
            self.image.set_alpha(180 if self.blink_timer % 4 < 2 else 255)
            self.blink_timer += 1
            return  # 冰冻状态不执行任何移动

        if not self.enemy:
            self._player_control(keys, walls, tanks)
        else:
            self._enemy_ai(walls, tanks, player)

        self._keep_in_bounds()

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def _can_move(self, dx, dy, walls, tanks=None):
        """检查是否可以移动"""
        new_rect = self.rect.copy()
        new_rect.x += dx
        new_rect.y += dy

        if (new_rect.left < 0 or new_rect.right > SCREEN_WIDTH or
            new_rect.top < 0 or new_rect.bottom > SCREEN_HEIGHT):
            return False

        if walls:
            for wall in walls:
                if new_rect.colliderect(wall.rect):
                    return False

        if tanks:
            for tank in tanks:
                if tank != self and new_rect.colliderect(tank.rect):
                    return False

        return True

    def _player_control(self, keys, walls=None, tanks=None):
        """玩家控制"""
        dx, dy = 0, 0
        old_dir = self.direction

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.speed
            self.direction = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.speed
            self.direction = "down"
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.speed
            self.direction = "left"
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.speed
            self.direction = "right"

        if dx != 0 or dy != 0:
            if self._can_move(dx, dy, walls, tanks):
                self.rect.x += dx
                self.rect.y += dy
            elif dx != 0 and self._can_move(dx, 0, walls, tanks):
                self.rect.x += dx
            elif dy != 0 and self._can_move(0, dy, walls, tanks):
                self.rect.y += dy

        if self.direction != old_dir:
            self.update_image()

    def _keep_in_bounds(self):
        """确保坦克不超出窗口边界"""
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def _enemy_ai(self, walls=None, tanks=None, player=None):
        """敌方AI"""
        old_dir = self.direction

        if random.randint(0, 100) < 1:
            if player and random.random() < 0.4:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                self.direction = "right" if abs(dx) > abs(dy) and dx > 0 else \
                                 "left" if abs(dx) > abs(dy) else \
                                 "down" if dy > 0 else "up"
            else:
                self.direction = random.choice(["up", "down", "left", "right"])

        dx, dy = 0, 0
        if self.direction == "up":
            dy = -self.speed // 2
        elif self.direction == "down":
            dy = self.speed // 2
        elif self.direction == "left":
            dx = -self.speed // 2
        elif self.direction == "right":
            dx = self.speed // 2

        if not self._can_move(dx, dy, walls, tanks):
            self.direction = random.choice(["up", "down", "left", "right"])
        else:
            self.rect.x += dx
            self.rect.y += dy

        if self.direction != old_dir:
            self.update_image()

    def shoot(self):
        """发射子弹，返回列表（升级后可双发）"""
        if self.shoot_cooldown > 0:
            return []

        bx, by = self.rect.center
        bullets = []

        # 子弹速度和强化属性
        if not self.enemy and self.upgrade_level >= 1:
            speed = 14  # 快速子弹
            powered = (self.upgrade_level >= 3)  # 等级3可摧毁钢铁
        else:
            speed = BULLET_SPEED  # 默认 10
            powered = False

        if self.direction == "up":
            by -= self.height // 2 + 5
        elif self.direction == "down":
            by += self.height // 2 + 5
        elif self.direction == "left":
            bx -= self.width // 2 + 5
        elif self.direction == "right":
            bx += self.width // 2 + 5

        # 等级2+：双发并行
        if not self.enemy and self.upgrade_level >= 2:
            offset = 7
            if self.direction in ("up", "down"):
                bullets.append(Bullet(bx - offset, by, self.direction, speed=speed, enemy=self.enemy, powered=powered))
                bullets.append(Bullet(bx + offset, by, self.direction, speed=speed, enemy=self.enemy, powered=powered))
            else:
                bullets.append(Bullet(bx, by - offset, self.direction, speed=speed, enemy=self.enemy, powered=powered))
                bullets.append(Bullet(bx, by + offset, self.direction, speed=speed, enemy=self.enemy, powered=powered))
        else:
            bullets.append(Bullet(bx, by, self.direction, speed=speed, enemy=self.enemy, powered=powered))

        self.shoot_cooldown = self.max_cooldown
        return bullets