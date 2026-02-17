import pygame
import random
import sys

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

# 坦克类
class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed=5):
        super().__init__()
        # 坦克大小
        self.width = 40
        self.height = 40
        # 创建坦克表面（矩形）
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.direction = "up"

    def update(self, keys=None):
        # 玩家坦克控制
        if keys:
            self._player_control(keys)
        # 敌方坦克简单AI（随机移动）
        else:
            self._enemy_ai()
        
        self._keep_in_bounds()

    def _player_control(self, keys):
        """玩家坦克控制逻辑"""
        # 上下左右移动
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= self.speed
            self.direction = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += self.speed
            self.direction = "down"
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.direction = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.direction = "right"

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

    def _enemy_ai(self):
        """简单的敌方AI：随机移动"""
        # 随机改变移动方向（降低频率）
        if random.randint(0, 100) < 2:
            directions = ["up", "down", "left", "right"]
            self.direction = random.choice(directions)
        
        # 根据方向移动
        if self.direction == "up":
            self.rect.y -= self.speed // 2  # 敌方速度慢一点
        elif self.direction == "down":
            self.rect.y += self.speed // 2
        elif self.direction == "left":
            self.rect.x -= self.speed // 2
        elif self.direction == "right":
            self.rect.x += self.speed // 2

# 主游戏函数
def main():
    # 创建游戏窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("基础版坦克大战")
    
    # 时钟（控制帧率）
    clock = pygame.time.Clock()
    
    # 创建精灵组
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    # 创建玩家坦克（蓝色）
    player_tank = Tank(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, BLUE)
    all_sprites.add(player_tank)

    for _ in range(3):
        enemy_x = random.randint(50, SCREEN_WIDTH-50)
        enemy_y = random.randint(50, SCREEN_HEIGHT//2)
        enemy_tank = Tank(enemy_x, enemy_y, RED)
        all_sprites.add(enemy_tank)
        enemies.add(enemy_tank)

    running = True
    while running:
        clock.tick(FPS)
        # 1. 事件处理（必须加，否则窗口关不掉）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 3. 绘制画面（必须加，否则看不到坦克）
        screen.fill(BLACK)  # 先清空背景
        all_sprites.draw(screen)  # 绘制坦克

        # 获取按键状态（用于持续移动）
        keys = pygame.key.get_pressed()

        player_tank.update(keys)  # 玩家坦克传入按键
        for enemy in enemies:
            enemy.update()  # 敌方坦克无需按键

        # 4. 更新显示
        pygame.display.flip() 

# 程序入口
if __name__ == "__main__":
    main()