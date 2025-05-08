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
            # double size
            self.image = pygame.transform.scale(self.original_image, (w*2, h*2))
            # keep bottom-center in place
            midbottom = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom=midbottom)
            self.grown = True

    def update(self, platforms, powerups):
        self.handle_input()

        # horizontal movement & collisions
        self.rect.x += self.vel.x
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for plat in hits:
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right

        # vertical movement & collisions
        self.apply_gravity()
        self.rect.y += self.vel.y
        hits = pygame.sprite.spritecollide(self, platforms, False)
        self.on_ground = False
        for plat in hits:
            if self.vel.y > 0:
                self.rect.bottom = plat.rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = plat.rect.bottom
                self.vel.y = 0

        # power‑up collision
        pu_hits = pygame.sprite.spritecollide(self, powerups, True)
        if pu_hits:
            self.grow()

# — Platform Sprite —
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0, 255, 0))  # green block
        self.rect = self.image.get_rect(topleft=(x, y))

# — Dumbbell Power‑Up Sprite —
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # create transparent surface
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # draw two end‑caps (circles) and a bar between them
        cap_radius = 8
        bar_rect = pygame.Rect(cap_radius, size//2 - 4, size - 2*cap_radius, 8)
        pygame.draw.rect(self.image, (80, 80, 80), bar_rect)
        pygame.draw.circle(self.image, (80, 80, 80), (cap_radius, size//2), cap_radius)
        pygame.draw.circle(self.image, (80, 80, 80), (size - cap_radius, size//2), cap_radius)
        self.rect = self.image.get_rect(center=(x, y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer with Power‑Up")
    clock = pygame.time.Clock()

    all_sprites = pygame.sprite.Group()
    platforms   = pygame.sprite.Group()
    powerups    = pygame.sprite.Group()

    # player
    player = Player(100, SCREEN_HEIGHT - 150)
    all_sprites.add(player)

    # ground
    ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    platforms.add(ground)
    all_sprites.add(ground)

    # floating platforms
    for x, y, w, h in [(200, 450, 100, 20), (400, 350, 120, 20), (650, 300, 80, 20)]:
        plat = Platform(x, y, w, h)
        platforms.add(plat)
        all_sprites.add(plat)

    # place one dumbbell power‑up
    dumbbell = PowerUp(300, 420)
    powerups.add(dumbbell)
    all_sprites.add(dumbbell)

    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False

        # update includes checking for power‑up collision
        player.update(platforms, powerups)

        screen.fill(BG_COLOR)
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
