"""
关卡过渡动画模块
在每一关结束后播放过渡动画
"""
import pygame
import random
import math

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


class Particle:
    """粒子特效"""
    def __init__(self, x, y, color, speed, angle, size, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.angle = angle
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size < 1:
            size = 1
        # 创建带 alpha 的表面
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(surf, color_with_alpha, (size, size), size)
        screen.blit(surf, (int(self.x) - size, int(self.y) - size))


class Star:
    """闪烁的星星"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(50, 255)
        self.speed = random.uniform(0.5, 2.0)
        self.phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.phase += 0.03 * self.speed
        self.brightness = 128 + int(127 * math.sin(self.phase))

    def draw(self, screen):
        if self.brightness > 0:
            alpha = min(self.brightness, 255)
            surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, alpha),
                             (self.size, self.size), self.size)
            screen.blit(surf, (int(self.x) - self.size, int(self.y) - self.size))


class LevelTransition:
    """关卡过渡动画"""
    def __init__(self, level, score, screen):
        self.level = level
        self.score = score
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.timer = 0
        self.duration = 480  # 8秒 (60 FPS * 8)
        
        # 粒子系统
        self.particles = []
        self._create_explosion_particles()
        
        # 星星背景
        self.stars = [Star() for _ in range(50)]
        
        # 大字动画
        self.title_scale = 0.0
        self.title_y_offset = -50
        
        # 信息动画
        self.info_alpha = 0
        
        # 提示动画
        self.tip_blink = 0
        
        # 已完成标志
        self.finished = False
        
        # 字体
        self.font_large = pygame.font.SysFont("simhei", 64)
        self.font_medium = pygame.font.SysFont("simhei", 36)
        self.font_small = pygame.font.SysFont("simhei", 24)

    def _create_explosion_particles(self):
        """创建开场爆炸粒子"""
        colors = [YELLOW, ORANGE, RED, WHITE]
        for _ in range(60):
            x = SCREEN_WIDTH // 2 + random.randint(-200, 200)
            y = SCREEN_HEIGHT // 2 + random.randint(-200, 200)
            color = random.choice(colors)
            speed = random.uniform(1, 5)
            angle = random.uniform(0, math.pi * 2)
            size = random.randint(2, 6)
            lifetime = random.randint(30, 80)
            self.particles.append(Particle(x, y, color, speed, angle, size, lifetime))

    def _create_celebration_particles(self):
        """创建庆祝粒子（飘落）"""
        colors = [YELLOW, ORANGE, RED, GREEN, CYAN, PURPLE, WHITE]
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = -random.randint(10, 100)
            color = random.choice(colors)
            speed = random.uniform(2, 6)
            angle = math.pi / 2 + random.uniform(-0.5, 0.5)
            size = random.randint(3, 8)
            lifetime = random.randint(60, 150)
            self.particles.append(Particle(x, y, color, speed, angle, size, lifetime))

    def update(self):
        """更新过渡动画"""
        self.timer += 1
        
        # 更新星星
        for star in self.stars:
            star.update()
        
        # 更新粒子
        self.particles = [p for p in self.particles if p.update()]
        
        # 持续生成庆祝粒子
        if random.random() < 0.3:
            self._create_celebration_particles()
        
        # 大字动画：逐渐放大并回落
        progress = min(self.timer / 60, 1.0)
        self.title_scale = progress * (2.0 - progress)  # 缓出效果
        self.title_y_offset = -50 * (1 - progress)  # 从上方滑入
        
        # 信息渐入
        if self.timer > 30:
            self.info_alpha = min((self.timer - 30) * 8, 255)
        
        # 闪烁提示
        self.tip_blink = (self.timer % 60) < 30
        
        # 检查是否结束
        if self.timer >= self.duration:
            self.finished = True

    def draw(self):
        """绘制过渡画面"""
        self.screen.fill(BLACK)
        
        # 绘制星星背景
        for star in self.stars:
            star.draw(self.screen)
        
        # 绘制粒子
        for particle in self.particles:
            particle.draw(self.screen)
        
        # 绘制标题（放大滑动效果）
        title_text = f"第 {self.level} 关"
        if self.level > 5:
            title_text = "最终关"
        
        # 使用缩放渲染
        base_surf = self.font_large.render(title_text, True, YELLOW)
        scaled_size = (
            int(base_surf.get_width() * self.title_scale),
            int(base_surf.get_height() * self.title_scale)
        )
        if scaled_size[0] > 0 and scaled_size[1] > 0:
            scaled_surf = pygame.transform.scale(base_surf, scaled_size)
            title_rect = scaled_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60 + self.title_y_offset)
            )
            self.screen.blit(scaled_surf, title_rect)
        
        # 副标题
        subtitle_text = "准备战斗！"
        if self.level > 5:
            subtitle_text = "BOSS战！"
        elif self.level > 3:
            subtitle_text = "难度升级！"
        
        if self.info_alpha > 0:
            subtitle_surf = self.font_medium.render(subtitle_text, True, ORANGE)
            subtitle_surf.set_alpha(self.info_alpha)
            subtitle_rect = subtitle_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
            )
            self.screen.blit(subtitle_surf, subtitle_rect)
        
        # 显示当前得分
        if self.info_alpha > 0:
            score_text = f"当前得分: {self.score}"
            score_surf = self.font_small.render(score_text, True, WHITE)
            score_surf.set_alpha(self.info_alpha)
            score_rect = score_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
            )
            self.screen.blit(score_surf, score_rect)
        
        # 闪烁提示
        if self.tip_blink:
            tip_text = f"关卡 {self.level} 将在 {max(1, (self.duration - self.timer) // 60 + 1)} 秒后开始... (按 O 跳过)"
            tip_surf = self.font_small.render(tip_text, True, GRAY)
            tip_rect = tip_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
            )
            self.screen.blit(tip_surf, tip_rect)

    def run(self):
        """运行动画循环，返回是否完成"""
        # 清空残留事件，防止上一轮的按键（如空格）跳过动画
        pygame.event.clear()
        
        run_anim = True
        while run_anim:
            self.clock.tick(FPS)
            
            # 事件处理（允许跳过）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        run_anim = False
            
            self.update()
            self.draw()
            pygame.display.flip()
            
            if self.finished:
                run_anim = False
        
        return True  # 动画完成


# 简单测试
def test():
    """测试过渡动画"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("关卡过渡动画测试")
    
    transition = LevelTransition(1, 1200, screen)
    result = transition.run()
    print(f"动画结果: {result}")
    
    pygame.quit()

if __name__ == "__main__":
    test()