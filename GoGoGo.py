import pygame
import random
import sys
import os
from pygame.locals import *

# 初始化Pygame
pygame.init()

# 游戏常量
BASE_WIDTH = 1000
BASE_HEIGHT = 400
GRAVITY = 0.8
JUMP_POWER = -15
PLAYER_SPEED = 5
BASE_SCROLL_SPEED = 5
SPEED_INCREASE = 0.001
OBSTACLE_INTERVAL = 1500
SCALE_FACTOR = 1.0  # 初始缩放比例

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, screen_height):
        super().__init__()
        self.screen_height = screen_height
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        original_image = pygame.image.load(os.path.join(base_path, 'resources/dino.svg')).convert_alpha()
        self.normal_image = pygame.transform.scale(original_image, 
            (int(original_image.get_width() * SCALE_FACTOR), 
             int(original_image.get_height() * SCALE_FACTOR)))
        self.crouch_image = pygame.transform.scale(self.normal_image, 
            (int(40 * SCALE_FACTOR), int(30 * SCALE_FACTOR)))
        self.image = self.normal_image
        self.rect = self.image.get_rect(midleft=(100, screen_height // 2))
        self.vel_y = 0
        self.is_crouching = False
        self.on_ground = True

    def update(self):
        # 应用重力
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # 地面检测
        if self.rect.bottom >= self.screen_height - 50:
            self.rect.bottom = self.screen_height - 50
            self.vel_y = 0
            self.on_ground = True

        # 更新形象
        if self.is_crouching:
            self.image = self.crouch_image
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
        else:
            self.image = self.normal_image
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def jump(self):
        if self.on_ground and not self.is_crouching:
            self.vel_y = JUMP_POWER
            self.on_ground = False


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, type, screen_width, screen_height):
        super().__init__()
        self.type = type
        if type == "high":
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            original_image = pygame.image.load(os.path.join(base_path, 'resources/cactus_high.svg')).convert_alpha()
            self.image = pygame.transform.scale(original_image, 
                (int(original_image.get_width() * SCALE_FACTOR),
                 int(original_image.get_height() * SCALE_FACTOR)))
            y_pos = screen_height - int(120 * SCALE_FACTOR)
        else:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            original_image = pygame.image.load(os.path.join(base_path, 'resources/cactus_low.svg')).convert_alpha()
            self.image = pygame.transform.scale(original_image, 
                (int(original_image.get_width() * SCALE_FACTOR),
                 int(original_image.get_height() * SCALE_FACTOR)))
            y_pos = screen_height - int(80 * SCALE_FACTOR)  # 调整低障碍物高度
        self.rect = self.image.get_rect(midleft=(screen_width, y_pos))
        print(f'生成障碍物 类型:{type} 坐标:{self.rect}')


class Coin(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.image = pygame.Surface((int(20 * SCALE_FACTOR), int(20 * SCALE_FACTOR)))
        self.image.fill(GOLD)
        max_jump_height = (abs(JUMP_POWER)**2) / (2 * GRAVITY) * SCALE_FACTOR
        ground_level = screen_height - int(50 * SCALE_FACTOR)
        y_pos = random.randint(int(ground_level - max_jump_height), int(ground_level - 20 * SCALE_FACTOR))
        self.rect = self.image.get_rect(center=(screen_width, y_pos))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), FULLSCREEN)
        self.fullscreen = True
        self.actual_width, self.actual_height = self.screen.get_size()
        pygame.display.set_caption("GoGoGo")

        # 游戏状态
        self.running = True
        self.game_over = False
        self.restart_time = 0
        self.score = 0

        # 初始化游戏对象
        self.init_game()

    def init_game(self):
        self.player = Player(self.actual_height)
        self.all_sprites = pygame.sprite.Group(self.player)
        self.obstacles = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.scroll_speed = BASE_SCROLL_SPEED
        self.last_obstacle_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((0, 0), FULLSCREEN)
        self.actual_width, self.actual_height = self.screen.get_size()
        self.init_game()  # 重置游戏以适应新尺寸

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_F11:
                    self.toggle_fullscreen()
                elif event.key == K_UP:
                    self.player.jump()
                elif event.key == K_DOWN:
                    self.player.is_crouching = True
                elif event.key == K_ESCAPE:
                    self.running = False
                elif self.game_over and pygame.time.get_ticks() - self.restart_time > 3000:
                    self.init_game()
                    self.game_over = False
                    self.score = 0
            elif event.type == KEYUP and event.key == K_DOWN:
                self.player.is_crouching = False

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            current_time = pygame.time.get_ticks()
            self.handle_events()

            if not self.game_over:
                # 速度控制
                keys = pygame.key.get_pressed()
                # 自动增速和距离计分
                self.scroll_speed = BASE_SCROLL_SPEED + (pygame.time.get_ticks() // 1000) * 0.2
                self.score += int(self.scroll_speed * 0.5)

                # 生成障碍物和金币
                if current_time - self.last_obstacle_time > OBSTACLE_INTERVAL:
                    self.last_obstacle_time = current_time
                    if random.random() < 0.7:
                        obstacle = Obstacle(random.choice(["high", "low"]), self.actual_width, self.actual_height)
                        self.obstacles.add(obstacle)
                        self.all_sprites.add(obstacle)
                    else:
                        coin = Coin(self.actual_width, self.actual_height)
                        self.coins.add(coin)
                        self.all_sprites.add(coin)

                # 更新位置
                for sprite in self.all_sprites:
                    if isinstance(sprite, (Obstacle, Coin)):
                        sprite.rect.x -= self.scroll_speed
                        if sprite.rect.right < 0:
                            sprite.kill()

                self.player.update()

                # 碰撞检测
                for obstacle in self.obstacles:
                    if pygame.sprite.collide_rect(self.player, obstacle):
                        collision_valid = obstacle.type in ['high', 'low']
                        if collision_valid:
                            print(f'碰撞发生！类型:{obstacle.type} 下蹲状态:{self.player.is_crouching}')
                            self.game_over = True
                            self.restart_time = pygame.time.get_ticks()
                            
                            # 绘制碰撞框
                            pygame.draw.rect(self.screen, RED, self.player.rect, 2)
                            pygame.draw.rect(self.screen, RED, obstacle.rect, 2)

                # 金币收集
                for coin in pygame.sprite.spritecollide(self.player, self.coins, True):
                    self.score += 10

            # 渲染
            # 绘制动态背景
            self.screen.fill((245, 245, 245))
            for i in range(3):
                pygame.draw.rect(self.screen, (200, 200, 200), (0, self.actual_height - int(50 * SCALE_FACTOR) + i*int(5 * SCALE_FACTOR), self.actual_width, int(2 * SCALE_FACTOR)))
            self.all_sprites.draw(self.screen)

            # 显示分数
            score_text = self.font.render(f"Score: {self.score}", True, BLACK)
            self.screen.blit(score_text, (10, 10))

            # 游戏结束提示
            if self.game_over:
                if pygame.time.get_ticks() - self.restart_time > 3000:
                    text = self.font.render("Press any key to restart", True, BLACK)
                else:
                    text = self.font.render("Game Over!", True, RED)
                text_rect = text.get_rect(center=(self.actual_width // 2, self.actual_height // 2))
                self.screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()