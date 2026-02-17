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


    def update(self, keys=None):
        pass




# 主游戏函数
def main():
    # 创建游戏窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("基础版坦克大战")
    
    # 时钟（控制帧率）
    clock = pygame.time.Clock()
    
    # 创建精灵组
    all_sprites = pygame.sprite.Group()
    
    # 创建玩家坦克（蓝色）
    player_tank = Tank(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, BLUE)
    all_sprites.add(player_tank)

    running = True
    while running:
        # 1. 事件处理（必须加，否则窗口关不掉）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 3. 绘制画面（必须加，否则看不到坦克）
        screen.fill(BLACK)  # 先清空背景
        all_sprites.draw(screen)  # 绘制坦克

        # 4. 更新显示
        pygame.display.flip() 

# 程序入口
if __name__ == "__main__":
    main()