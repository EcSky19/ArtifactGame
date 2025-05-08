import pygame
import sys

# — Constants —
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
BG_COLOR = (135, 206, 235)  # sky blue

# — Player Sprite —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.original_image = pygame.Surface((40, 50), pygame.SRCALPHA)
        self.original_image.fill((255, 0, 0))  # red block
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

    def take_damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 60  # 1 second at 60 FPS
            print(f"Ouch! Health: {self.health}")

    def update(self, platforms, powerups, enemies):
        # Decrease invincibility timer
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.handle_input()

        # Horizontal movement & collisions
        self.rect.x += self.vel.x
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right

        # Vertical movement & collisions
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

        # Power-up collision
        if pygame.sprite.spritecollide(self, powerups, True):
            self.grow()

        # Enemy collision
        if pygame.sprite.spritecollide(self, enemies, False):
            self.take_damage()

# — Platform Sprite —
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0, 255, 0))  # green block
        self.rect = self.image.get_rect(topleft=(x, y))

# — Dumbbell Power-Up Sprite —
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        cap_radius = 8
        bar_rect = pygame.Rect(cap_radius, size//2 - 4, size - 2*cap_radius, 8)
        pygame.draw.rect(self.image, (80, 80, 80), bar_rect)
        pygame.draw.circle(self.image, (80, 80, 80), (cap_radius, size//2), cap_radius)
        pygame.draw.circle(self.image, (80, 80, 80), (size - cap_radius, size//2), cap_radius)
        self.rect = self.image.get_rect(center=(x, y))

# — Enemy Sprite (Homework) —
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 40
        self.image = pygame.Surface((size, size))
        self.image.fill((255, 255, 255))  # white block
        pygame.draw.rect(self.image, (0, 0, 0), self.image.get_rect(), 2)
        font = pygame.font.Font(None, 24)
        txt = font.render("HW", True, (0, 0, 0))
        txt_rect = txt.get_rect(center=(size//2, size//2))
        self.image.blit(txt, txt_rect)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        # Placeholder for future movement/animation
        pass

# — Main Game Loop —
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer with Enemies")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    all_sprites = pygame.sprite.Group()
    platforms   = pygame.sprite.Group()
    powerups    = pygame.sprite.Group()
    enemies     = pygame.sprite.Group()

    # Create player
    player = Player(100, SCREEN_HEIGHT - 150)
    all_sprites.add(player)

    # Ground platform
    ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    platforms.add(ground)
    all_sprites.add(ground)

    # Floating platforms
    for x, y, w, h in [(200, 450, 100, 20), (400, 350, 120, 20), (650, 300, 80, 20)]:
        plat = Platform(x, y, w, h)
        platforms.add(plat)
        all_sprites.add(plat)

    # Place power-up
    dumbbell = PowerUp(300, 420)
    powerups.add(dumbbell)
    all_sprites.add(dumbbell)

    # Create enemies
    for x, y in [(500, SCREEN_HEIGHT - 80), (350, 310)]:
        enemy = Enemy(x, y)
        enemies.add(enemy)
        all_sprites.add(enemy)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update only dynamic sprites with correct arguments
        player.update(platforms, powerups, enemies)
        enemies.update()
        powerups.update()

        # Draw everything
        screen.fill(BG_COLOR)
        all_sprites.draw(screen)

        # Display health
        health_text = font.render(f"Health: {player.health}", True, (255, 0, 0))
        screen.blit(health_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
