"""
精灵模块
包含所有游戏角色的类定义：坦克、子弹、墙壁、爆炸效果
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
    """钢铁墙 - 不可摧毁"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TANK_SIZE, TANK_SIZE))
        self.image.fill(GRAY)
        pygame.draw.rect(self.image, WHITE, (0, 0, TANK_SIZE, TANK_SIZE), 2)
        pygame.draw.rect(self.image, DARK_GRAY, (5, 5, 30, 30))
        pygame.draw.circle(self.image, WHITE, (20, 20), 8, 2)
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


class Bullet(pygame.sprite.Sprite):
    """子弹"""
    def __init__(self, x, y, direction, speed=BULLET_SPEED, enemy=False):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.direction = direction
        self.enemy = enemy

        # 子弹外观
        if enemy:
            self.image.fill(RED)
            pygame.draw.circle(self.image, YELLOW, (4, 4), 3)
        else:
            self.image.fill(YELLOW)
            pygame.draw.circle(self.image, WHITE, (4, 4), 3)

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


class Tank(pygame.sprite.Sprite):
    """坦克基类（玩家和敌人共用）"""
    def __init__(self, x, y, color, speed=PLAYER_SPEED, enemy=False):
        super().__init__()
        self.width = TANK_SIZE
        self.height = TANK_SIZE
        self.color = color
        self.speed = speed
        self.direction = "up"
        self.shoot_cooldown = 0
        self.max_cooldown = 15
        self.enemy = enemy
        self.lives = PLAYER_LIVES if not enemy else 1

        self.image = pygame.Surface((self.width, self.height))
        self.original_color = color
        self.update_image()

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.invincible_time = 0
        self.blink_timer = 0

    def update_image(self):
        """更新坦克图像，包括炮管方向"""
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.color)

        # 画履带
        pygame.draw.rect(self.image, DARK_GRAY, (2, 2, 8, 36))
        pygame.draw.rect(self.image, DARK_GRAY, (30, 2, 8, 36))
        for i in range(0, 36, 6):
            pygame.draw.rect(self.image, (80, 80, 80), (3, i + 2, 6, 3))
            pygame.draw.rect(self.image, (80, 80, 80), (31, i + 2, 6, 3))

        # 炮塔底座
        pygame.draw.circle(self.image, self.color, (20, 20), 12)
        pygame.draw.circle(self.image, WHITE, (20, 20), 10, 1)
        pygame.draw.circle(self.image, DARK_GRAY, (20, 20), 8)

        # 画炮管
        barrel_length = 18
        barrel_width = 6

        if self.direction == "up":
            pygame.draw.rect(self.image, GRAY, (17, 2, barrel_width, barrel_length))
        elif self.direction == "down":
            pygame.draw.rect(self.image, GRAY, (17, 20, barrel_width, barrel_length))
        elif self.direction == "left":
            pygame.draw.rect(self.image, GRAY, (2, 17, barrel_length, barrel_width))
        elif self.direction == "right":
            pygame.draw.rect(self.image, GRAY, (20, 17, barrel_length, barrel_width))

    def update(self, keys=None, walls=None, tanks=None, player=None):
        """更新状态"""
        # 无敌闪烁
        if self.invincible_time > 0:
            self.invincible_time -= 1
            self.blink_timer += 1
            self.image.set_alpha(128 if self.blink_timer % 6 < 3 else 255)
        else:
            self.image.set_alpha(255)

        if keys:
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
        """发射子弹"""
        if self.shoot_cooldown == 0:
            bullet_x, bullet_y = self.rect.center
            if self.direction == "up":
                bullet_y -= self.height // 2 + 5
            elif self.direction == "down":
                bullet_y += self.height // 2 + 5
            elif self.direction == "left":
                bullet_x -= self.width // 2 + 5
            elif self.direction == "right":
                bullet_x += self.width // 2 + 5

            bullet = Bullet(bullet_x, bullet_y, self.direction, enemy=self.enemy)
            self.shoot_cooldown = self.max_cooldown
            return bullet
        return None