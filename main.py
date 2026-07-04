"""
坦克大战游戏 - 主入口
启动游戏，初始化窗口并进入游戏循环
"""
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from game_manager import GameManager


def main():
    """游戏主入口 - 初始化并启动游戏"""
    pygame.init()
    pygame.display.set_caption("坦克大战")
    # 禁用输入法文本处理，防止中文输入法拦截 WASD 等按键
    pygame.key.stop_text_input()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    game = GameManager(screen)
    game.run()


if __name__ == "__main__":
    main()