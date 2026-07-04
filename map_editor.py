"""
地图编辑器模块
支持自定义砖墙、钢铁墙、水地、老窝位置
保存为 JSON 文件，可在开始界面选择加载
"""
import json
import pygame
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TANK_SIZE
from sprites import BrickWall, SteelWall, Water, Base

# 网格尺寸
COLS = SCREEN_WIDTH // TANK_SIZE    # 20
ROWS = SCREEN_HEIGHT // TANK_SIZE   # 15

# 地图文件路径
MAP_FILE = "custom_map.json"

# 编辑模式中的单元格类型
EMPTY = 0
BRICK = 1
STEEL = 2
WATER = 3
BASE = 4
SPAWN = 5  # 玩家出生点（只能有一个）

# 类型名称和颜色（用于编辑界面显示）
CELL_NAMES = {
    EMPTY: "空地",
    BRICK: "砖墙",
    STEEL: "钢墙",
    WATER: "水地",
    BASE: "老窝",
    SPAWN: "出生点",
}


def create_default_map():
    """创建默认地图（空模板，只含老窝保护墙）"""
    grid = [[EMPTY] * COLS for _ in range(ROWS)]

    # 老窝位置 (col=10, row=14)
    grid[14][10] = BASE
    # 老窝周围砖墙保护 3x3 格
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            if dr == 0 and dc == 0:
                continue
            r, c = 14 + dr, 10 + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                grid[r][c] = BRICK

    # 玩家出生点 (col=8, row=14)
    grid[14][8] = SPAWN

    return grid


def save_map(grid, filename=MAP_FILE):
    """保存地图到 JSON 文件"""
    data = {
        "rows": ROWS,
        "cols": COLS,
        "grid": grid,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_map(filename=MAP_FILE):
    """从 JSON 文件加载地图，失败返回 None"""
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["grid"]
    except Exception:
        return None


def grid_to_sprites(grid, walls_group, waters_group, bases_group):
    """将网格数据转换为游戏精灵，返回玩家出生点坐标"""
    spawn_pos = None
    for row in range(ROWS):
        for col in range(COLS):
            cell = grid[row][col]
            x = col * TANK_SIZE
            y = row * TANK_SIZE
            if cell == BRICK:
                wall = BrickWall(x, y)
                walls_group.add(wall)
            elif cell == STEEL:
                wall = SteelWall(x, y)
                walls_group.add(wall)
            elif cell == WATER:
                water = Water(x, y)
                waters_group.add(water)
            elif cell == BASE:
                base = Base(x + TANK_SIZE // 2, y + TANK_SIZE // 2)
                bases_group.add(base)
            elif cell == SPAWN:
                spawn_pos = (x + TANK_SIZE // 2, y + TANK_SIZE // 2)
    return spawn_pos


class MapEditor:
    """地图编辑器"""
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("simhei", 18)
        self.font_medium = pygame.font.SysFont("simhei", 22)

        # 加载已有地图或创建默认
        loaded = load_map()
        self.grid = loaded if loaded else create_default_map()
        self.current_type = BRICK
        self.running = True
        self.message = ""
        self.message_timer = 0

        # 右侧面板占用屏幕右侧区域
        self.panel_x = SCREEN_WIDTH - 150

    def run(self):
        """运行编辑器主循环，返回是否使用自定义地图"""
        result = False
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                result = self._handle_event(event) or result

            self._draw()
            pygame.display.flip()

        return result

    def _handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

            # 数字键切换放置类型
            elif event.key == pygame.K_1:
                self.current_type = BRICK
            elif event.key == pygame.K_2:
                self.current_type = STEEL
            elif event.key == pygame.K_3:
                self.current_type = WATER
            elif event.key == pygame.K_4:
                self.current_type = BASE
            elif event.key == pygame.K_5:
                self.current_type = EMPTY
            elif event.key == pygame.K_6:
                self.current_type = SPAWN

            # S 键保存
            elif event.key == pygame.K_s:
                save_map(self.grid)
                self.message = "地图已保存!"
                self.message_timer = 90

            # 空格/回车使用当前地图开始游戏
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                has_spawn = any(SPAWN in row for row in self.grid)
                has_base = any(BASE in row for row in self.grid)
                if not has_spawn:
                    self.grid[14][8] = SPAWN
                if not has_base:
                    self.grid[14][10] = BASE
                save_map(self.grid)
                self.running = False
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            # 忽略点击面板区域
            if pos[0] >= self.panel_x:
                return False
            col = pos[0] // TANK_SIZE
            row = pos[1] // TANK_SIZE
            if 0 <= col < COLS and 0 <= row < ROWS:
                if event.button == 1:  # 左键放置
                    if self.current_type == BASE:
                        for r in range(ROWS):
                            for c in range(COLS):
                                if self.grid[r][c] == BASE:
                                    self.grid[r][c] = EMPTY
                    if self.current_type == SPAWN:
                        for r in range(ROWS):
                            for c in range(COLS):
                                if self.grid[r][c] == SPAWN:
                                    self.grid[r][c] = EMPTY
                    self.grid[row][col] = self.current_type
                elif event.button == 3:  # 右键擦除
                    self.grid[row][col] = EMPTY

        return False

    def _draw(self):
        """绘制编辑器界面"""
        self.screen.fill((20, 20, 20))

        # 绘制网格
        for row in range(ROWS):
            for col in range(COLS):
                x = col * TANK_SIZE
                y = row * TANK_SIZE
                cell = self.grid[row][col]
                rect = pygame.Rect(x, y, TANK_SIZE, TANK_SIZE)

                if cell == BRICK:
                    pygame.draw.rect(self.screen, (139, 69, 19), rect)
                    for br in range(4):
                        for bc in range(4):
                            off = 5 if br % 2 == 0 else 0
                            off_x = x + bc * 10 + off
                            if off_x < self.panel_x:
                                pygame.draw.rect(self.screen, (160, 82, 45),
                                               (off_x, y + br * 10, 9, 9))
                elif cell == STEEL:
                    pygame.draw.rect(self.screen, (128, 128, 128), rect)
                    pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
                    if x + 5 < self.panel_x:
                        pygame.draw.rect(self.screen, (80, 80, 80), (x + 5, y + 5, 30, 30))
                        pygame.draw.circle(self.screen, (200, 200, 200),
                                         (x + 20, y + 20), 8, 2)
                elif cell == WATER:
                    self.screen.fill((0, 100, 180), rect)
                    for i in range(0, TANK_SIZE, 8):
                        off = (i // 8) % 2
                        for j in range(off, TANK_SIZE, 16):
                            if x + j + 12 < self.panel_x:
                                pygame.draw.ellipse(self.screen, (50, 150, 220),
                                                   (x + j, y + i, 12, 6))
                                pygame.draw.ellipse(self.screen, (100, 200, 255),
                                                   (x + j + 2, y + i + 2, 8, 2))
                elif cell == BASE:
                    cx, cy = x + TANK_SIZE // 2, y + TANK_SIZE // 2
                    pygame.draw.rect(self.screen, (100, 100, 100),
                                   (cx - 12, cy + 6, 24, 10))
                    pygame.draw.rect(self.screen, (180, 180, 180),
                                   (cx - 1, cy - 12, 3, 20))
                    flag_pts = [(cx + 2, cy - 12), (cx + 16, cy - 7), (cx + 2, cy - 2)]
                    pygame.draw.polygon(self.screen, (255, 200, 0), flag_pts)
                    pygame.draw.circle(self.screen, (255, 255, 0), (cx + 7, cy - 7), 2)
                elif cell == SPAWN:
                    pygame.draw.rect(self.screen, (0, 60, 0), rect)
                    pygame.draw.rect(self.screen, (0, 255, 0), (x + 8, y + 8, 24, 24), 2)
                    pygame.draw.circle(self.screen, (0, 200, 0), (x + 20, y + 20), 6)

                pygame.draw.rect(self.screen, (60, 60, 60), rect, 1)

        # 绘制右侧面板
        self._draw_panel()

    def _draw_panel(self):
        """绘制右侧控制面板"""
        px = self.panel_x + 5
        y = 10

        # 半透明背景
        panel_bg = pygame.Surface((145, SCREEN_HEIGHT))
        panel_bg.set_alpha(200)
        panel_bg.fill((30, 30, 30))
        self.screen.blit(panel_bg, (self.panel_x, 0))

        # 标题
        title = self.font_medium.render("地图编辑器", True, (255, 255, 0))
        self.screen.blit(title, (px, y))
        y += 30

        # 当前选中类型
        sel_text = f"当前: {CELL_NAMES.get(self.current_type, '?')}"
        sel = self.font_small.render(sel_text, True, (255, 255, 255))
        self.screen.blit(sel, (px, y))
        y += 25

        # 类型选择
        types = [
            ("1", "砖墙", BRICK),
            ("2", "钢墙", STEEL),
            ("3", "水地", WATER),
            ("4", "老窝", BASE),
            ("5", "擦除", EMPTY),
            ("6", "出生点", SPAWN),
        ]
        for key, name, cell_type in types:
            color = (255, 255, 0) if cell_type == self.current_type else (200, 200, 200)
            surf = self.font_small.render(f"{key} - {name}", True, color)
            self.screen.blit(surf, (px, y))
            y += 22

        y += 10
        tips = [
            "左键: 放置",
            "右键: 擦除",
            "",
            "S: 保存地图",
            "空格: 开始游戏",
            "ESC: 退出",
        ]
        for text in tips:
            surf = self.font_small.render(text, True, (150, 150, 150))
            self.screen.blit(surf, (px, y))
            y += 20

        # 统计
        y = SCREEN_HEIGHT - 80
        brick_count = sum(row.count(BRICK) for row in self.grid)
        steel_count = sum(row.count(STEEL) for row in self.grid)
        water_count = sum(row.count(WATER) for row in self.grid)
        stats = f"砖:{brick_count}"
        self.screen.blit(self.font_small.render(stats, True, (200, 200, 200)), (px, y))
        y += 18
        stats = f"钢:{steel_count}"
        self.screen.blit(self.font_small.render(stats, True, (200, 200, 200)), (px, y))
        y += 18
        stats = f"水:{water_count}"
        self.screen.blit(self.font_small.render(stats, True, (200, 200, 200)), (px, y))

        # 保存提示
        if self.message_timer > 0:
            self.message_timer -= 1
            msg = self.font_small.render(self.message, True, (0, 255, 0))
            self.screen.blit(msg, (px, 10))