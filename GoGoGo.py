import pygame
import random
import sys
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

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, screen_height):
        super().__init__()
        self.screen_height = screen_height
        self.normal_image = pygame.image.load('resources/dino.svg').convert_alpha()
        self.crouch_image = pygame.transform.scale(self.normal_image, (40, 30))
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
            self.image = pygame.image.load('resources/cactus_high.svg').convert_alpha()
            y_pos = screen_height - 120
        else:
            self.image = pygame.image.load('resources/cactus_low.svg').convert_alpha()
            y_pos = screen_height - 80  # 需要下蹲的高度
        self.rect = self.image.get_rect(midleft=(screen_width, y_pos))


class Coin(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(GOLD)
        y_pos = random.randint(100, screen_height - 100)
        self.rect = self.image.get_rect(center=(screen_width, y_pos))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), RESIZABLE)
        self.fullscreen = False
        self.actual_width = BASE_WIDTH
        self.actual_height = BASE_HEIGHT
        pygame.display.set_caption("横版闯关游戏")

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
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), RESIZABLE)
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
                        collision_valid = (obstacle.type == "low")
                        if not collision_valid:
                            self.game_over = True
                            self.restart_time = pygame.time.get_ticks()

                # 金币收集
                for coin in pygame.sprite.spritecollide(self.player, self.coins, True):
                    self.score += 10

            # 渲染
            # 绘制动态背景
            self.screen.fill((245, 245, 245))
            for i in range(3):
                pygame.draw.rect(self.screen, (200, 200, 200), (0, self.actual_height-50 + i*5, self.actual_width, 2))
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