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
from sprites import Tank, BrickWall, SteelWall, Water, Explosion, Bullet, PowerUp, Base
from level_transition import LevelTransition
from map_editor import grid_to_sprites, load_map, MAP_FILE, MapEditor
from sounds import SoundManager


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
        self.waters = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.bases = pygame.sprite.Group()

        # 玩家
        self.player_tank = None
        self.gun_powered = False  # 手枪道具强化状态

        # 音效
        self.sound = SoundManager()

        # 初始化第一关
        self._init_level()

    # ========== 初始化方法 ==========

    def _init_level(self):
        """初始化当前关卡"""
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.walls.empty()
        self.waters.empty()
        self.explosions.empty()
        self.powerups.empty()
        self.bases.empty()

        # 创建玩家（黄色，原版风格）- 出生在老窝左侧
        spawn_col = 8
        spawn_row = 14
        self.player_tank = Tank(
            spawn_col * TANK_SIZE + TANK_SIZE // 2,
            spawn_row * TANK_SIZE + TANK_SIZE // 2,
            YELLOW
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
        # 水地（不可通过但子弹可穿过，数量和钢铁墙差不多）
        water_positions = [
            (200, 200), (400, 200), (600, 200),
            (80, 360), (240, 360), (480, 360), (680, 360),
            (360, 480), (520, 480),
        ]
        for x, y in water_positions:
            if random.random() < 0.5:
                water = Water(x, y)
                self.waters.add(water)
                self.all_sprites.add(water)

        # 砖墙（避开玩家出生区域和底部老窝区域）
        for row in range(3, 10):
            for col in range(2, 18):
                px, py = col * TANK_SIZE, row * TANK_SIZE
                if (row + col) % 2 == 1 and random.random() < 0.4:
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

        # 生成老窝（屏幕底部中间，对齐网格）
        base_col = 10
        base_row = 14
        bx = base_col * TANK_SIZE + TANK_SIZE // 2
        by = base_row * TANK_SIZE + TANK_SIZE // 2
        base = Base(bx, by)
        self.bases.add(base)
        self.all_sprites.add(base)

        # 老窝周围一圈保护（3x3 格，老窝在正中央）
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue  # 老窝自身位置不留墙
                wx = (base_col + dc) * TANK_SIZE
                wy = (base_row + dr) * TANK_SIZE
                if 0 <= wx < SCREEN_WIDTH and 0 <= wy < SCREEN_HEIGHT:
                    # 老窝正前方（上方）为钢铁墙，其余为砖墙
                    if dr == -1 and dc == 0:
                        wall = SteelWall(wx, wy)
                    else:
                        wall = BrickWall(wx, wy)
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
                for water in self.waters:
                    if new_rect.colliderect(water.rect):
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
                        self.sound.play('shoot')
                        if not bullet.enemy and self.gun_powered:
                            # 替换为强化子弹：速度2倍，可摧毁钢铁墙
                            self.bullets.remove(bullet)
                            self.all_sprites.remove(bullet)
                            bullet = Bullet(bullet.rect.centerx, bullet.rect.centery,
                                           bullet.direction, bullet.speed, enemy=False, powered=True)
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

        # 玩家更新（水和墙都是坦克不可通过的障碍，但拥有船道具时可以进入水）
        all_tanks = [self.player_tank] + list(self.enemies)
        full_obstacles = list(self.walls) + list(self.waters)
        if self.player_tank.boat_mode:
            player_obstacles = list(self.walls)  # 有船时可以无视水面
        else:
            player_obstacles = full_obstacles
        self.player_tank.update(keys, player_obstacles, all_tanks)

        # 敌人更新 + 自动射击（敌人始终不能进入水面）
        for enemy in self.enemies:
            enemy.update(None, full_obstacles, all_tanks, self.player_tank)
            if random.randint(0, 100) < 3:
                bullet = enemy.shoot()
                if bullet:
                    self.sound.play('enemy_shoot')
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

    def enable_gun(self):
        """手枪道具：子弹强化，可摧毁钢铁墙"""
        self.gun_powered = True

    def enable_boat(self):
        """船道具：可进入水面"""
        self.player_tank.boat_mode = True

    def freeze_enemies(self):
        """冰冻所有敌人5秒"""
        for enemy in self.enemies:
            enemy.frozen_time = 300  # 5秒

    def add_life(self):
        """奖一条命"""
        self.player_tank.lives += 1

    def bomb_all_enemies(self):
        """炸死全部敌人"""
        self.sound.play('explosion')
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
            self.sound.play('powerup')
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
                        self.sound.play('wall_hit')
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

            # 任何子弹击中老窝 → 游戏结束
            if bullet.alive() and self.bases:
                for base in list(self.bases):
                    if bullet.rect.colliderect(base.rect):
                        base.kill()
                        bullet.kill()
                        self.sound.play('base_destroyed')
                        self.sound.stop_bgm()
                        explosion = Explosion(base.rect.centerx, base.rect.centery, size=TANK_SIZE)
                        self.all_sprites.add(explosion)
                        self.explosions.add(explosion)
                        self.game_over = True
                        break

        # 坦克（敌方/玩家）碰到老窝也游戏结束
        if self.bases:
            for base in list(self.bases):
                if not base.alive:
                    continue
                # 敌方坦克碰到老窝
                for enemy in self.enemies:
                    if enemy.rect.colliderect(base.rect):
                        base.kill()
                        self.sound.play('base_destroyed')
                        self.sound.stop_bgm()
                        explosion = Explosion(base.rect.centerx, base.rect.centery, size=TANK_SIZE)
                        self.all_sprites.add(explosion)
                        self.explosions.add(explosion)
                        self.game_over = True
                        break
                if self.game_over:
                    break

    def _on_enemy_hit(self, bullet, enemy):
        """玩家子弹击中敌人"""
        bullet.kill()
        enemy.kill()
        self.score += 100
        self.sound.play('explosion')
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
        self.sound.play('explosion')

        explosion = Explosion(self.player_tank.rect.centerx, self.player_tank.rect.centery)
        self.all_sprites.add(explosion)
        self.explosions.add(explosion)

        if self.player_tank.lives <= 0:
            self.game_over = True
            self.sound.play('game_over')
            self.sound.stop_bgm()
        else:
            spawn_col = 8
            spawn_row = 14
            self.player_tank.rect.center = (
                spawn_col * TANK_SIZE + TANK_SIZE // 2,
                spawn_row * TANK_SIZE + TANK_SIZE // 2
            )
            self.player_tank.invincible_time = INVINCIBLE_TIME

    def _on_wall_hit(self, bullet, walls_hit):
        """子弹击中墙壁"""
        bullet.kill()
        self.sound.play('wall_hit')
        for wall in walls_hit:
            if hasattr(wall, 'hit'):
                # 强化子弹可以摧毁钢铁墙，普通子弹不能
                if getattr(wall, 'steel', False) and not bullet.powered:
                    continue
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
            self.sound.play('victory')
            self.sound.stop_bgm()
            return

        # 播放过渡动画
        transition = LevelTransition(self.level, self.score, self.screen)
        result = transition.run()
        if not result:
            self.running = False
            return

        # 清除残留道具、强化状态和旧地图，防止带到下一关
        self.gun_powered = False
        for pu in list(self.powerups):
            pu.kill()
        self.powerups.empty()
        self.walls.empty()
        self.waters.empty()
        self.bases.empty()
        self.all_sprites.empty()

        # 重新生成完整地图
        self._generate_map()

        # 重置并重新添加玩家到老窝左侧出生点
        spawn_col = 8
        spawn_row = 14
        self.player_tank = Tank(
            spawn_col * TANK_SIZE + TANK_SIZE // 2,
            spawn_row * TANK_SIZE + TANK_SIZE // 2,
            YELLOW
        )
        self.player_tank.lives = PLAYER_LIVES
        self.all_sprites.add(self.player_tank)

        # 重新添加所有地图精灵
        for wall in self.walls:
            self.all_sprites.add(wall)
        for water in self.waters:
            self.all_sprites.add(water)
        for base in self.bases:
            self.all_sprites.add(base)

        # 生成新敌人
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

    def _init_custom_level(self):
        """使用自定义地图初始化关卡"""
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.walls.empty()
        self.waters.empty()
        self.explosions.empty()
        self.powerups.empty()
        self.bases.empty()

        grid = load_map()
        if grid is None:
            return False

        spawn_pos = grid_to_sprites(grid, self.walls, self.waters, self.bases)
        if spawn_pos:
            sx, sy = spawn_pos
        else:
            sx, sy = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80

        self.player_tank = Tank(sx, sy, YELLOW)
        self.player_tank.lives = PLAYER_LIVES
        self.all_sprites.add(self.player_tank)

        # 把所有自定义精灵加入 all_sprites
        for wall in self.walls:
            self.all_sprites.add(wall)
        for water in self.waters:
            self.all_sprites.add(water)
        for base in self.bases:
            self.all_sprites.add(base)

        self._spawn_enemies()
        return True

    def draw_start_screen(self):
        """开始界面"""
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        waiting = False
                        self.sound.play('game_start')
                    if event.key == pygame.K_c:
                        # 进入自定义地图编辑器
                        editor = MapEditor(self.screen)
                        result = editor.run()
                        if result:
                            # 使用自定义地图开始游戏
                            self._init_custom_level()
                            return
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return

            self.screen.fill(BLACK)

            # 绘制网格背景
            for x in range(0, SCREEN_WIDTH, TANK_SIZE):
                pygame.draw.line(self.screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, TANK_SIZE):
                pygame.draw.line(self.screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))

            # 标题
            title = self.font_large.render("坦 克 大 战", True, YELLOW)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(title, title_rect)

            # 装饰线条
            pygame.draw.line(self.screen, YELLOW, (200, 210), (600, 210), 2)

            # 操作说明
            controls = [
                "WASD / 方向键   移动",
                "空格    射击",
                "P    暂停",
                "O    跳过关卡动画",
            ]
            y_offset = 270
            for text in controls:
                surf = self.font_small.render(text, True, WHITE)
                rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                self.screen.blit(surf, rect)
                y_offset += 35

            # 自定义地图选项
            has_custom = load_map() is not None
            if has_custom:
                custom_text = "按 C - 编辑/使用自定义地图 (已保存)"
            else:
                custom_text = "按 C - 创建自定义地图"
            c_surf = self.font_small.render(custom_text, True, (0, 200, 255))
            c_rect = c_surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 20))
            self.screen.blit(c_surf, c_rect)

            # 闪烁提示
            blink = (pygame.time.get_ticks() // 600) % 2 == 0
            if blink:
                tip = self.font_medium.render("按 空格 或 回车 开始游戏", True, (0, 255, 0))
                tip_rect = tip.get_rect(center=(SCREEN_WIDTH // 2, 500))
                self.screen.blit(tip, tip_rect)

            pygame.display.flip()

    def run(self):
        """主游戏循环"""
        # 显示开始界面
        self.draw_start_screen()
        if not self.running:
            pygame.quit()
            sys.exit()

        # 开始背景音乐
        self.sound.play_bgm()

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
