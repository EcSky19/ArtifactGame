import pygame
import sys

# — Constants —
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
BG_COLOR = (135, 206, 235)  # sky blue

# — Player Sprite (Human‑like) —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        self.original_image = pygame.Surface((w, h), pygame.SRCALPHA)
        # Draw head
        head_radius = 8
        pygame.draw.circle(self.original_image, (255, 224, 189), (w//2, head_radius), head_radius)
        # Draw body
        body_rect = pygame.Rect(w//2 - 5, head_radius*2, 10, h - head_radius*2)
        pygame.draw.rect(self.original_image, (0, 0, 255), body_rect)
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.grown = False
        self.health = 3
        self.invincible_timer = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vel.x = PLAYER_SPEED
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = JUMP_VELOCITY

    def apply_gravity(self):
        self.vel.y += GRAVITY
        if self.vel.y > 15:
            self.vel.y = 15

    def grow(self):
        if not self.grown:
            w, h = self.original_image.get_size()
            self.image = pygame.transform.scale(self.original_image, (w*2, h*2))
            midbottom = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom=midbottom)
            self.grown = True

    def shrink(self):
        if self.grown:
            midbottom = self.rect.midbottom
            self.image = self.original_image
            self.rect = self.image.get_rect(midbottom=midbottom)
            self.grown = False

    def take_damage(self):
        if self.invincible_timer <= 0:
            # Shrink if powered-up
            if self.grown:
                self.shrink()
            self.health -= 1
            self.invincible_timer = FPS  # 1 second

    def update(self, platforms, powerups, enemies):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.handle_input()
        # Horizontal collisions
        self.rect.x += self.vel.x
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right

        # Vertical collisions
        self.apply_gravity()
        self.rect.y += self.vel.y
        self.on_ground = False
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.y > 0:
                self.rect.bottom = plat.rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = plat.rect.bottom
                self.vel.y = 0

        # Power-up
        if pygame.sprite.spritecollide(self, powerups, True):
            self.grow()
        # Enemy
        if pygame.sprite.spritecollide(self, enemies, False):
            self.take_damage()

# — Platform Sprite —
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

# — Dumbbell Power-Up —
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        cap = 8
        pygame.draw.rect(self.image, (80, 80, 80), (cap, size//2-4, size-2*cap, 8))
        pygame.draw.circle(self.image, (80, 80, 80), (cap, size//2), cap)
        pygame.draw.circle(self.image, (80, 80, 80), (size-cap, size//2), cap)
        self.rect = self.image.get_rect(center=(x, y))

# — Enemy Sprite (Homework Patrol) —
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_width=120, speed=2):
        super().__init__()
        size = 40
        self.image = pygame.Surface((size, size))
        self.image.fill((255, 255, 255))
        pygame.draw.rect(self.image, (0, 0, 0), self.image.get_rect(), 2)
        font = pygame.font.Font(None, 24)
        txt = font.render("HW", True, (0, 0, 0))
        self.image.blit(txt, txt.get_rect(center=(size//2, size//2)))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.patrol_width = patrol_width
        self.speed = speed
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x > self.start_x + self.patrol_width or self.rect.x < self.start_x:
            self.direction *= -1

# — Show Game Over Screen —
def show_game_over(screen, font):
    screen.fill((0, 0, 0))
    text = font.render("Game Over", True, (255, 0, 0))
    rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(text, rect)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

# — Main Game Loop —
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer with Patrol Enemies")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 72)

    platforms = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    player = Player(100, SCREEN_HEIGHT - 150)
    platforms.add(Platform(0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40))
    for x, y, w, h in [(200,450,100,20),(400,350,120,20),(650,300,80,20)]:
        platforms.add(Platform(x,y,w,h))
    powerups.add(PowerUp(300,420))
    enemies.add(Enemy(500, SCREEN_HEIGHT-80, patrol_width=150))
    enemies.add(Enemy(350, 310, patrol_width=80, speed=3))

    all_sprites = pygame.sprite.Group(platforms, powerups, enemies, player)
    small_font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(platforms, powerups, enemies)
        enemies.update()

        if player.health <= 0:
            show_game_over(screen, font)
            running = False

        screen.fill(BG_COLOR)
        all_sprites.draw(screen)
        screen.blit(small_font.render(f"Health: {player.health}", True, (255,0,0)), (10,10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()