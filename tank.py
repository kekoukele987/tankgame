import pygame
import random
import sys
import math
from level_transition import LevelTransition

# 初始化pygame
pygame.init()

# 游戏常量定义
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义（RGB）
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# 砖墙类
class BrickWall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BROWN)
        # 画砖纹
        for row in range(4):
            for col in range(4):
                offset = 5 if row % 2 == 0 else 0
                pygame.draw.rect(self.image, (160, 82, 45),
                               (col * 10 + offset, row * 10, 9, 9))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.health = 3  # 砖墙生命值

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

# 钢铁墙类（不可摧毁）
class SteelWall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(GRAY)
        # 画金属质感
        pygame.draw.rect(self.image, WHITE, (0, 0, 40, 40), 2)
        pygame.draw.rect(self.image, DARK_GRAY, (5, 5, 30, 30))
        pygame.draw.circle(self.image, WHITE, (20, 20), 8, 2)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# 爆炸效果类
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size=40):
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
        
        # 从黄色到红色的渐变爆炸效果
        color_ratio = self.frame / self.max_frame
        r = 255
        g = int(255 * (1 - color_ratio))
        b = 0
        
        pygame.draw.circle(self.image, (r, g, b, alpha),
                         (self.size // 2, self.size // 2), radius)
        pygame.draw.circle(self.image, (255, 255, 200, alpha),
                         (self.size // 2, self.size // 2), radius // 2)

# 坦克基类
class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed=5, enemy=False):
        super().__init__()
        self.width = 40
        self.height = 40
        self.color = color
        self.speed = speed
        self.direction = "up"
        self.shoot_cooldown = 0
        self.max_cooldown = 15
        self.enemy = enemy
        self.lives = 3 if not enemy else 1
        
        # 创建坦克图像
        self.image = pygame.Surface((self.width, self.height))
        self.original_color = color
        self.update_image()
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # 无敌时间（重生后）
        self.invincible_time = 0
        self.blink_timer = 0

    def update_image(self):
        """更新坦克图像，包括炮管方向"""
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.color)
        
        # 画履带
        track_color = DARK_GRAY
        # 左右履带
        pygame.draw.rect(self.image, track_color, (2, 2, 8, 36))
        pygame.draw.rect(self.image, track_color, (30, 2, 8, 36))
        # 履带纹理
        for i in range(0, 36, 6):
            pygame.draw.rect(self.image, (80, 80, 80), (3, i + 2, 6, 3))
            pygame.draw.rect(self.image, (80, 80, 80), (31, i + 2, 6, 3))
        
        # 炮塔底座（圆形）
        pygame.draw.circle(self.image, self.color, (20, 20), 12)
        pygame.draw.circle(self.image, WHITE, (20, 20), 10, 1)
        pygame.draw.circle(self.image, DARK_GRAY, (20, 20), 8)
        
        # 画炮管
        barrel_length = 18
        barrel_width = 6
        barrel_color = GRAY
        
        if self.direction == "up":
            pygame.draw.rect(self.image, barrel_color,
                           (17, 2, barrel_width, barrel_length))
        elif self.direction == "down":
            pygame.draw.rect(self.image, barrel_color,
                           (17, 20, barrel_width, barrel_length))
        elif self.direction == "left":
            pygame.draw.rect(self.image, barrel_color,
                           (2, 17, barrel_length, barrel_width))
        elif self.direction == "right":
            pygame.draw.rect(self.image, barrel_color,
                           (20, 17, barrel_length, barrel_width))

    def update(self, keys=None, walls=None, tanks=None, player=None):
        # 更新无敌闪烁
        if self.invincible_time > 0:
            self.invincible_time -= 1
            self.blink_timer += 1
            if self.blink_timer % 6 < 3:  # 闪烁效果
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
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
        """检查是否可以移动到新位置"""
        new_rect = self.rect.copy()
        new_rect.x += dx
        new_rect.y += dy
        
        # 检查边界
        if (new_rect.left < 0 or new_rect.right > SCREEN_WIDTH or
            new_rect.top < 0 or new_rect.bottom > SCREEN_HEIGHT):
            return False
        
        # 检查墙壁碰撞
        if walls:
            for wall in walls:
                if new_rect.colliderect(wall.rect):
                    return False
        
        # 检查坦克碰撞
        if tanks:
            for tank in tanks:
                if tank != self and new_rect.colliderect(tank.rect):
                    return False
        
        return True

    def _player_control(self, keys, walls=None, tanks=None):
        """玩家坦克控制"""
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
            # 尝试沿当前方向移动
            if self._can_move(dx, dy, walls, tanks):
                self.rect.x += dx
                self.rect.y += dy
            # 如果不能，尝试只沿一个方向移动（贴墙滑动）
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
        """敌方AI：追击玩家并射击"""
        old_dir = self.direction
        
        # 随机转向
        if random.randint(0, 100) < 1:
            # 有一定概率朝玩家方向走
            if player and random.random() < 0.4:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                if abs(dx) > abs(dy):
                    self.direction = "right" if dx > 0 else "left"
                else:
                    self.direction = "down" if dy > 0 else "up"
            else:
                self.direction = random.choice(["up", "down", "left", "right"])
        
        # 移动
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

# 子弹类
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed=10, enemy=False):
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
        
        # 子弹超出窗口则销毁
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

# 游戏主函数
def main():
    # 创建游戏窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("坦克大战")
    
    # 时钟
    clock = pygame.time.Clock()
    
    # 字体
    font_large = pygame.font.SysFont("simhei", 48)
    font_medium = pygame.font.SysFont("simhei", 32)
    font_small = pygame.font.SysFont("simhei", 20)
    
    # 游戏状态
    score = 0
    level = 1
    game_over = False
    victory = False
    paused = False
    
    # 按键状态（用于菜单）
    key_state = {}
    
    # 预声明游戏对象变量
    all_sprites = None
    enemies = None
    bullets = None
    walls = None
    player_tank = None
    explosions = None
    
    def init_level():
        """初始化关卡"""
        nonlocal all_sprites, enemies, bullets, walls, player_tank, explosions
        
        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        walls = pygame.sprite.Group()
        explosions = pygame.sprite.Group()
        
        # 创建玩家坦克
        player_tank = Tank(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80, BLUE, speed=5)
        player_tank.lives = 3
        all_sprites.add(player_tank)
        
        # 生成地图障碍物
        generate_map()
        
        # 生成敌人
        spawn_enemies()
    
    def reset_game():
        """重置游戏状态"""
        nonlocal score, level, game_over, victory
        score = 0
        level = 1
        game_over = False
        victory = False
        init_level()
    
    def generate_map():
        """生成地图障碍物"""
        # 在中间区域生成砖墙（避开玩家出生区域）
        for row in range(3, 10):
            for col in range(2, 18):
                # 避开玩家出生区域（屏幕底部中央）
                px, py = col * 40, row * 40
                if py >= 440 and px >= 280 and px <= 520:
                    continue
                if (row + col) % 3 == 0 and random.random() < 0.25:
                    wall = BrickWall(px, py)
                    walls.add(wall)
                    all_sprites.add(wall)
        
        # 在四周添加一些钢铁墙
        steel_positions = [
            (120, 120), (360, 80), (600, 120),
            (80, 280), (680, 280),
            (200, 400), (560, 400),
        ]
        for x, y in steel_positions:
            if random.random() < 0.5:
                wall = SteelWall(x, y)
                walls.add(wall)
                all_sprites.add(wall)
    
    def spawn_enemies():
        """生成敌人"""
        enemy_count = min(4 + level, 8)  # 随关卡增加敌人数量
        
        for _ in range(enemy_count):
            while True:
                # 在屏幕上方区域生成
                enemy_x = random.randint(60, SCREEN_WIDTH - 60)
                enemy_y = random.randint(40, 200)
                
                # 检查生成位置是否与现有坦克重叠
                new_rect = pygame.Rect(enemy_x - 20, enemy_y - 20, 40, 40)
                collision = False
                if player_tank and new_rect.colliderect(player_tank.rect):
                    collision = True
                for enemy in enemies:
                    if new_rect.colliderect(enemy.rect):
                        collision = True
                        break
                
                if not collision:
                    break
            
            enemy_tank = Tank(enemy_x, enemy_y, RED, speed=4, enemy=True)
            all_sprites.add(enemy_tank)
            enemies.add(enemy_tank)
    
    # 初始化游戏
    init_level()
    
    running = True
    while running:
        clock.tick(FPS)
        
        # 1. 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over and not victory and not paused:
                    bullet = player_tank.shoot()
                    if bullet:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                
                if event.key == pygame.K_p:
                    paused = not paused
                
                if event.key == pygame.K_r and (game_over or victory):
                    reset_game()
                
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        if paused:
            # 显示暂停
            screen.fill(BLACK)
            pause_text = font_large.render("暂停", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, 250))
            tip_text = font_small.render("按 P 继续", True, WHITE)
            screen.blit(tip_text, (SCREEN_WIDTH//2 - tip_text.get_width()//2, 320))
            pygame.display.flip()
            continue
        
        if game_over or victory:
            # 绘制游戏结束或胜利画面
            screen.fill(BLACK)
            
            if game_over:
                title_text = font_large.render("游戏结束", True, RED)
            else:
                title_text = font_large.render("恭喜通关！", True, GREEN)
            
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 150))
            
            score_text = font_medium.render(f"最终得分: {score}", True, YELLOW)
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 250))
            
            level_text = font_medium.render(f"到达关卡: {level}", True, WHITE)
            screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 310))
            
            tip_text = font_small.render("按 R 重新开始 | 按 ESC 退出", True, WHITE)
            screen.blit(tip_text, (SCREEN_WIDTH//2 - tip_text.get_width()//2, 400))
            
            pygame.display.flip()
            continue
        
        # 2. 更新游戏逻辑
        keys = pygame.key.get_pressed()
        
        # 玩家更新
        all_tanks = [player_tank] + list(enemies)
        player_tank.update(keys, walls, all_tanks)
        
        # 敌人更新
        for enemy in enemies:
            enemy.update(None, walls, all_tanks, player_tank)
            
            # 敌方坦克自动射击
            if random.randint(0, 100) < 3:
                bullet = enemy.shoot()
                if bullet:
                    all_sprites.add(bullet)
                    bullets.add(bullet)
        
        # 子弹更新
        bullets.update()
        
        # 爆炸效果更新
        explosions.update()
        
        # 3. 碰撞检测
        players_bullet_hit = False
        
        for bullet in list(bullets):
            if not bullet.enemy:  # 玩家子弹
                # 击中敌人
                hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
                if hit_enemies:
                    bullet.kill()
                    hit_enemies[0].kill()
                    score += 100
                    explosion = Explosion(hit_enemies[0].rect.centerx, hit_enemies[0].rect.centery)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    continue
                
                # 击中墙壁
                hit_walls = pygame.sprite.spritecollide(bullet, walls, False)
                if hit_walls:
                    bullet.kill()
                    for wall in hit_walls:
                        if hasattr(wall, 'hit'):
                            wall.hit()
                    continue
            
            else:  # 敌方子弹
                # 击中玩家
                if (bullet.rect.colliderect(player_tank.rect) and 
                    player_tank.invincible_time <= 0 and not players_bullet_hit):
                    bullet.kill()
                    player_tank.lives -= 1
                    players_bullet_hit = True
                    explosion = Explosion(player_tank.rect.centerx, player_tank.rect.centery)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    
                    if player_tank.lives <= 0:
                        game_over = True
                    else:
                        player_tank.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
                        player_tank.invincible_time = 90
                    continue
                
                # 击中墙壁
                hit_walls = pygame.sprite.spritecollide(bullet, walls, False)
                if hit_walls:
                    bullet.kill()
                    for wall in hit_walls:
                        if hasattr(wall, 'hit'):
                            wall.hit()
                    continue
        
        # 敌人之间的碰撞检测
        enemies_list = list(enemies)
        for i, enemy1 in enumerate(enemies_list):
            for j, enemy2 in enumerate(enemies_list):
                if j > i and enemy1.rect.colliderect(enemy2.rect):
                    if enemy1.rect.centerx < enemy2.rect.centerx:
                        enemy1.rect.x -= 5
                        enemy2.rect.x += 5
                    else:
                        enemy1.rect.x += 5
                        enemy2.rect.x -= 5
                    if enemy1.rect.centery < enemy2.rect.centery:
                        enemy1.rect.y -= 5
                        enemy2.rect.y += 5
                    else:
                        enemy1.rect.y += 5
                        enemy2.rect.y -= 5
        
        # 检查是否通关
        if len(enemies) == 0:
            level += 1
            if level > 5:
                victory = True
            else:
                # 播放关卡过渡动画
                transition = LevelTransition(level, score, screen)
                result = transition.run()
                if not result:  # 用户关闭窗口
                    running = False
                # 生成新关卡
                spawn_enemies()
                score += 200
        
        # 4. 绘制画面
        screen.fill(BLACK)
        
        # 绘制网格背景
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))
        
        all_sprites.draw(screen)
        
        # 5. 绘制UI
        lives_text = font_small.render(f"生命: {player_tank.lives}", True, GREEN)
        screen.blit(lives_text, (10, 10))
        
        score_text = font_small.render(f"得分: {score}", True, YELLOW)
        screen.blit(score_text, (10, 35))
        
        level_text = font_small.render(f"关卡: {level}", True, WHITE)
        screen.blit(level_text, (10, 60))
        
        enemy_text = font_small.render(f"剩余敌人: {len(enemies)}", True, RED)
        screen.blit(enemy_text, (10, 85))
        
        controls_text = font_small.render("WASD/方向键移动 | 空格射击 | P暂停 | ESC退出", True, (100, 100, 100))
        screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, SCREEN_HEIGHT - 25))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

# 程序入口
if __name__ == "__main__":
    main()