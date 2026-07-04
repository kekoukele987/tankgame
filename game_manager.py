"""
游戏逻辑管理模块
负责游戏初始化、更新、碰撞检测、关卡管理、UI渲染等核心逻辑
"""
import pygame
import random
import sys
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TANK_SIZE,
    MAX_LEVEL, PLAYER_LIVES, INVINCIBLE_TIME,
    RED, BLUE, BLACK, WHITE, GREEN, YELLOW, GRAY
)
from sprites import Tank, BrickWall, SteelWall, Explosion, Bullet, PowerUp
from level_transition import LevelTransition


class GameManager:
    """游戏管理器，控制游戏整体流程"""

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        # 字体
        self.font_large = pygame.font.SysFont("simhei", 48)
        self.font_medium = pygame.font.SysFont("simhei", 32)
        self.font_small = pygame.font.SysFont("simhei", 20)

        # 游戏状态
        self.score = 0
        self.level = 1
        self.game_over = False
        self.victory = False
        self.paused = False
        self.running = True

        # 精灵组
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        # 玩家
        self.player_tank = None

        # 初始化第一关
        self._init_level()

    # ========== 初始化方法 ==========

    def _init_level(self):
        """初始化当前关卡"""
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.walls.empty()
        self.explosions.empty()
        self.powerups.empty()

        # 创建玩家（黄色，原版风格）
        self.player_tank = Tank(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80, YELLOW
        )
        self.player_tank.lives = PLAYER_LIVES
        self.all_sprites.add(self.player_tank)

        # 生成地图和敌人
        self._generate_map()
        self._spawn_enemies()

    def reset_game(self):
        """重置整个游戏"""
        self.score = 0
        self.level = 1
        self.game_over = False
        self.victory = False
        self._init_level()

    def _generate_map(self):
        """生成地图障碍物"""
        # 砖墙（避开玩家出生区域）
        for row in range(3, 10):
            for col in range(2, 18):
                px, py = col * TANK_SIZE, row * TANK_SIZE
                if py >= 440 and 280 <= px <= 520:
                    continue
                if (row + col) % 3 == 0 and random.random() < 0.25:
                    wall = BrickWall(px, py)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)

        # 钢铁墙
        steel_positions = [
            (120, 120), (360, 80), (600, 120),
            (80, 280), (680, 280),
            (200, 400), (560, 400),
        ]
        for x, y in steel_positions:
            if random.random() < 0.5:
                wall = SteelWall(x, y)
                self.walls.add(wall)
                self.all_sprites.add(wall)

    def _spawn_enemies(self):
        """生成敌人"""
        enemy_count = min(4 + self.level, 8)

        for _ in range(enemy_count):
            for _ in range(100):  # 最多尝试100次找一个空位
                ex = random.randint(60, SCREEN_WIDTH - 60)
                ey = random.randint(40, 200)
                new_rect = pygame.Rect(ex - 20, ey - 20, TANK_SIZE, TANK_SIZE)

                collision = False
                if self.player_tank and new_rect.colliderect(self.player_tank.rect):
                    collision = True
                for enemy in self.enemies:
                    if new_rect.colliderect(enemy.rect):
                        collision = True
                        break
                for wall in self.walls:
                    if new_rect.colliderect(wall.rect):
                        collision = True
                        break

                if not collision:
                    break

            enemy = Tank(ex, ey, RED, speed=4, enemy=True)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

    # ========== 事件处理 ==========

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

                if event.key == pygame.K_SPACE and not self._is_game_stopped():
                    bullet = self.player_tank.shoot()
                    if bullet:
                        self.all_sprites.add(bullet)
                        self.bullets.add(bullet)

                if event.key == pygame.K_p:
                    self.paused = not self.paused

                if event.key == pygame.K_r and (self.game_over or self.victory):
                    self.reset_game()

    def _is_game_stopped(self):
        """游戏是否处于暂停/结束/胜利状态"""
        return self.game_over or self.victory or self.paused

    # ========== 更新逻辑 ==========

    def update(self):
        """更新所有游戏逻辑"""
        keys = pygame.key.get_pressed()

        # 玩家更新
        all_tanks = [self.player_tank] + list(self.enemies)
        self.player_tank.update(keys, self.walls, all_tanks)

        # 敌人更新 + 自动射击
        for enemy in self.enemies:
            enemy.update(None, self.walls, all_tanks, self.player_tank)
            if random.randint(0, 100) < 3:
                bullet = enemy.shoot()
                if bullet:
                    self.all_sprites.add(bullet)
                    self.bullets.add(bullet)

        # 子弹和爆炸更新
        self.bullets.update()
        self.explosions.update()
        self.powerups.update()

        # 碰撞检测
        self._check_collisions()

        # 道具拾取检测
        self._check_powerup_pickup()

        # 敌人碰撞分离
        self._separate_enemies()

        # 通关检测
        self._check_level_clear()

    def freeze_enemies(self):
        """冰冻所有敌人5秒"""
        for enemy in self.enemies:
            enemy.frozen_time = 300  # 5秒

    def add_life(self):
        """奖一条命"""
        self.player_tank.lives += 1

    def bomb_all_enemies(self):
        """炸死全部敌人"""
        for enemy in list(self.enemies):
            explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
            self.all_sprites.add(explosion)
            self.explosions.add(explosion)
            self.score += 100
            enemy.kill()

    def _check_powerup_pickup(self):
        """检测玩家拾取道具"""
        if not self.player_tank:
            return
        hit = pygame.sprite.spritecollide(self.player_tank, self.powerups, True)
        for powerup in hit:
            powerup.apply(self)

    def _check_bullet_collision(self, player_bullet, enemy_bullet):
        """检测敌我子弹是否在同一条线上相向而行，是则抵消"""
        pb = player_bullet
        eb = enemy_bullet

        # 必须是相反方向
        opposite_pairs = [("up", "down"), ("down", "up"), ("left", "right"), ("right", "left")]
        if (pb.direction, eb.direction) not in opposite_pairs:
            return False

        # 垂直方向：x 坐标相近（在同一竖线上）
        if pb.direction in ("up", "down"):
            if abs(pb.rect.centerx - eb.rect.centerx) < 20:
                # 垂直方向有重叠或即将重叠
                if abs(pb.rect.centery - eb.rect.centery) < 30:
                    return True
        # 水平方向：y 坐标相近（在同一横线上）
        else:
            if abs(pb.rect.centery - eb.rect.centery) < 20:
                if abs(pb.rect.centerx - eb.rect.centerx) < 30:
                    return True

        return False

    def _check_collisions(self):
        """检测所有碰撞"""
        players_hit = False

        player_bullets = []
        enemy_bullets = []

        for bullet in list(self.bullets):
            if not bullet.enemy:
                player_bullets.append(bullet)
            else:
                enemy_bullets.append(bullet)

        # 敌我子弹抵消检测
        bullets_to_remove = set()
        for pb in player_bullets:
            for eb in enemy_bullets:
                if pb not in bullets_to_remove and eb not in bullets_to_remove:
                    if self._check_bullet_collision(pb, eb):
                        bullets_to_remove.add(pb)
                        bullets_to_remove.add(eb)
                        explosion = Explosion((pb.rect.centerx + eb.rect.centerx) // 2,
                                              (pb.rect.centery + eb.rect.centery) // 2,
                                              size=20)
                        self.all_sprites.add(explosion)
                        self.explosions.add(explosion)
                        break

        for bullet in bullets_to_remove:
            bullet.kill()

        for bullet in list(self.bullets):
            if bullet not in bullets_to_remove and not bullet.enemy:  # 玩家子弹
                # 击中敌人
                hit = pygame.sprite.spritecollide(bullet, self.enemies, False)
                if hit:
                    self._on_enemy_hit(bullet, hit[0])
                    continue

                # 击中墙壁
                hit = pygame.sprite.spritecollide(bullet, self.walls, False)
                if hit:
                    self._on_wall_hit(bullet, hit)

            elif bullet not in bullets_to_remove:  # 敌方子弹
                # 击中玩家
                if (bullet.rect.colliderect(self.player_tank.rect) and
                    self.player_tank.invincible_time <= 0 and not players_hit):
                    self._on_player_hit(bullet)
                    players_hit = True
                    continue

                # 击中墙壁
                hit = pygame.sprite.spritecollide(bullet, self.walls, False)
                if hit:
                    self._on_wall_hit(bullet, hit)

    def _on_enemy_hit(self, bullet, enemy):
        """玩家子弹击中敌人"""
        bullet.kill()
        enemy.kill()
        self.score += 100
        explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
        self.all_sprites.add(explosion)
        self.explosions.add(explosion)

        # 20%概率掉落道具
        if random.random() < 0.2:
            self._spawn_powerup(enemy.rect.centerx, enemy.rect.centery)

    def _spawn_powerup(self, x, y):
        """在指定位置生成道具"""
        powerup = PowerUp(x, y)
        self.powerups.add(powerup)
        self.all_sprites.add(powerup)

    def _on_player_hit(self, bullet):
        """敌方子弹击中玩家"""
        bullet.kill()
        self.player_tank.lives -= 1

        explosion = Explosion(self.player_tank.rect.centerx, self.player_tank.rect.centery)
        self.all_sprites.add(explosion)
        self.explosions.add(explosion)

        if self.player_tank.lives <= 0:
            self.game_over = True
        else:
            self.player_tank.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
            self.player_tank.invincible_time = INVINCIBLE_TIME

    def _on_wall_hit(self, bullet, walls_hit):
        """子弹击中墙壁"""
        bullet.kill()
        for wall in walls_hit:
            if hasattr(wall, 'hit'):
                wall.hit()

    def _separate_enemies(self):
        """防止敌人之间重叠"""
        enemies_list = list(self.enemies)
        for i, e1 in enumerate(enemies_list):
            for j, e2 in enumerate(enemies_list):
                if j > i and e1.rect.colliderect(e2.rect):
                    if e1.rect.centerx < e2.rect.centerx:
                        e1.rect.x -= 5
                        e2.rect.x += 5
                    else:
                        e1.rect.x += 5
                        e2.rect.x -= 5
                    if e1.rect.centery < e2.rect.centery:
                        e1.rect.y -= 5
                        e2.rect.y += 5
                    else:
                        e1.rect.y += 5
                        e2.rect.y -= 5

    def _check_level_clear(self):
        """检查是否通关"""
        if len(self.enemies) > 0:
            return

        self.level += 1
        if self.level > MAX_LEVEL:
            self.victory = True
            return

        # 播放过渡动画
        transition = LevelTransition(self.level, self.score, self.screen)
        result = transition.run()
        if not result:
            self.running = False
            return

        # 清除残留道具，防止带到下一关
        for pu in list(self.powerups):
            pu.kill()
        self.powerups.empty()

        # 重置玩家位置到屏幕下方中间
        self.player_tank.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        self.player_tank.direction = "up"
        self.player_tank.update_image()

        # 生成新关卡
        self._spawn_enemies()
        self.score += 200

    # ========== 绘制方法 ==========

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(BLACK)

        # 网格背景
        for x in range(0, SCREEN_WIDTH, TANK_SIZE):
            pygame.draw.line(self.screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, TANK_SIZE):
            pygame.draw.line(self.screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))

        # 精灵
        self.all_sprites.draw(self.screen)

        # UI
        self._draw_hud()

    def _draw_hud(self):
        """绘制HUD信息"""
        texts = [
            (f"生命: {self.player_tank.lives}", GREEN, 10, 10),
            (f"得分: {self.score}", YELLOW, 10, 35),
            (f"关卡: {self.level}", WHITE, 10, 60),
            (f"剩余敌人: {len(self.enemies)}", RED, 10, 85),
        ]
        for text, color, x, y in texts:
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (x, y))

        # 操作提示
        controls = "WASD/方向键移动 | 空格射击 | P暂停 | ESC退出"
        surf = self.font_small.render(controls, True, (100, 100, 100))
        cx = SCREEN_WIDTH // 2 - surf.get_width() // 2
        self.screen.blit(surf, (cx, SCREEN_HEIGHT - 25))

    def draw_pause(self):
        """绘制暂停界面"""
        self.screen.fill(BLACK)
        pause_text = self.font_large.render("暂停", True, WHITE)
        self.screen.blit(pause_text,
            (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 250))
        tip_text = self.font_small.render("按 P 继续", True, WHITE)
        self.screen.blit(tip_text,
            (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 320))

    def draw_game_over(self):
        """绘制游戏结束/胜利界面"""
        self.screen.fill(BLACK)

        if self.game_over:
            title = self.font_large.render("游戏结束", True, RED)
        else:
            title = self.font_large.render("恭喜通关！", True, GREEN)

        self.screen.blit(title,
            (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        score_text = self.font_medium.render(f"最终得分: {self.score}", True, YELLOW)
        self.screen.blit(score_text,
            (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 250))

        level_text = self.font_medium.render(f"到达关卡: {self.level}", True, WHITE)
        self.screen.blit(level_text,
            (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 310))

        tip_text = self.font_small.render("按 R 重新开始 | 按 ESC 退出", True, WHITE)
        self.screen.blit(tip_text,
            (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 400))

    def run(self):
        """主游戏循环"""
        while self.running:
            self.clock.tick(FPS)

            self.handle_events()
            if not self.running:
                break

            # 暂停
            if self.paused:
                self.draw_pause()
                pygame.display.flip()
                continue

            # 结束/胜利
            if self.game_over or self.victory:
                self.draw_game_over()
                pygame.display.flip()
                continue

            # 正常更新和绘制
            self.update()
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()