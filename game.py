import pygame
import sys

# — Constants —
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
PUCK_SPEED = 10
PUCK_LIFETIME = 60  # frames
SHOOT_COOLDOWN = 15  # frames between shots

# — Utility Functions —
def show_message(screen, font, text, color):
    screen.fill((0, 0, 0))
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(surf, rect)
    pygame.display.flip()
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                waiting = False

# — Sprite Classes —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        self.base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (255,224,189), (w//2,8), 8)
        pygame.draw.rect(self.base_image, (0,0,255), (w//2-5,16,10,h-16))
        self.helmet = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.arc(self.helmet, (200,200,0), (w//2-12,0,24,16), 3.14, 0, 4)
        self.has_hockey = False
        self.grown = False
        self.shoot_timer = 0
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.health = 3
        self.invincible_timer = 0
        self.facing = 1

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            self.vel.x = PLAYER_SPEED
            self.facing = 1
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = JUMP_VELOCITY

    def apply_gravity(self):
        self.vel.y = min(self.vel.y + GRAVITY, 15)

    def grow(self):
        if not self.grown:
            w, h = self.base_image.get_size()
            self.image = pygame.transform.scale(self.base_image, (w*2, h*2))
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.grown = True

    def lose_powerups(self):
        if self.has_hockey:
            self.has_hockey = False
        if self.grown:
            self.image = self.base_image.copy()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.grown = False

    def update(self, platforms, enemies, pucks_group, powerups_group):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        self.handle_input()
        self.rect.x += self.vel.x
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right
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
        for pu in pygame.sprite.spritecollide(self, powerups_group, True):
            if isinstance(pu, HockeyPowerUp):
                self.has_hockey = True
            elif isinstance(pu, DumbbellPowerUp):
                self.grow()
        if self.has_hockey and pygame.key.get_pressed()[pygame.K_q] and self.shoot_timer <= 0:
            pucks_group.add(Puck(self.rect.centerx, self.rect.centery, self.facing))
            self.shoot_timer = SHOOT_COOLDOWN
        for enemy in pygame.sprite.spritecollide(self, enemies, False):
            if self.vel.y > 0 and self.rect.bottom <= enemy.rect.top + 10:
                enemy.kill()
                self.vel.y = JUMP_VELOCITY
            elif self.invincible_timer <= 0:
                self.lose_powerups()
                self.health -= 1
                self.invincible_timer = FPS
        if self.has_hockey:
            self.image = self.base_image.copy()
            self.image.blit(self.helmet, (0,0))

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0,200,0))
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol, speed):
        super().__init__()
        size = 40
        self.image = pygame.Surface((size, size))
        self.image.fill((255,255,255))
        pygame.draw.rect(self.image, (0,0,0), self.image.get_rect(), 2)
        txt = pygame.font.Font(None,24).render("HW", True, (0,0,0))
        self.image.blit(txt, txt.get_rect(center=(size//2,size//2)))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x, self.range, self.speed, self.direction = x, patrol, speed, 1
    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.range:
            self.direction *= -1

class HockeyEnemy(Enemy):
    def __init__(self, x, y, patrol, speed):
        super().__init__(x, y, patrol, speed)
        self.shoot_timer = SHOOT_COOLDOWN
    def update(self):
        super().update()
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            pucks.add(Puck(self.rect.centerx, self.rect.centery, self.direction))
            self.shoot_timer = SHOOT_COOLDOWN

class Puck(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        size = 10
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0,0,0), (size//2,size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(PUCK_SPEED * direction, 0)
        self.lifetime = PUCK_LIFETIME
    def update(self):
        self.rect.x += self.vel.x
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class HockeyPowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 20
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0,0,0), (size//2,size//2), size//2)
        pygame.draw.circle(self.image, (255,255,255), (size//2,size//2), size//2-2)
        self.rect = self.image.get_rect(center=(x, y))

class DumbbellPowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size, cap = 30, 8
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (80,80,80), (cap, size//2-4, size-2*cap, 8))
        pygame.draw.circle(self.image, (80,80,80), (cap, size//2), cap)
        pygame.draw.circle(self.image, (80,80,80), (size-cap, size//2), cap)
        self.rect = self.image.get_rect(center=(x, y))

# — Main Game Loop —
def main():
    global pucks
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer")
    clock = pygame.time.Clock()
    big_font = pygame.font.Font(None, 72)

    # Load backgrounds
    try:
        bg_high = pygame.image.load('Images/highschool_bg.png').convert()
    except FileNotFoundError:
        bg_high = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_high.fill((200,200,200))
    try:
        bg_cornell = pygame.image.load('Images/cornell_bg.png').convert()
    except FileNotFoundError:
        bg_cornell = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_cornell.fill((180,50,50))
    try:
        bg_collegetown = pygame.image.load('Images/collegetown_bg.png').convert()  # Replace with your Collegetown background image
    except FileNotFoundError:
        bg_collegetown = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_collegetown.fill((100,150,100))  # greenish
    try:
        bg_lynah = pygame.image.load('Images/lynah_bg.png').convert()
    except FileNotFoundError:
        bg_lynah = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_lynah.fill((173,216,230))
    try:
        bg_gym = pygame.image.load('Images/gym_bg.png').convert()
    except FileNotFoundError:
        bg_gym = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_gym.fill((160,160,160))

    backgrounds = [
        pygame.transform.scale(b, (SCREEN_WIDTH, SCREEN_HEIGHT))
        for b in (bg_high, bg_cornell, bg_collegetown, bg_lynah, bg_gym)
    ]

    # Level data including Collegetown
    gap = 50
    levels = [
        {
            'platforms': [
                (0, 560, SCREEN_WIDTH - gap, 40),
                (200, 450, 100, 20),
                (400, 350, 120, 20),
                (650, 300, 80, 20)
            ],
            'enemies': [(500, 520, 150, 2), (350, 310, 80, 3)],
            'powerups': [(300, 520)]
        },
        {
            'platforms': [
                (gap, 560, SCREEN_WIDTH - 2 * gap, 40),
                (1000 - SCREEN_WIDTH, 450, 100, 20),
                (1200 - SCREEN_WIDTH, 350, 120, 20)
            ],
            'enemies': [(1100, 520, 100, 1)],
            'powerups': []
        },
        {
            'platforms': [(2 * gap, 560, SCREEN_WIDTH - 2 * gap, 40),
                          (2 * gap + 300, 450, 150, 20)],
            'enemies': [(2 * SCREEN_WIDTH + 200, 520, 100, 2),
                        (2 * SCREEN_WIDTH + 500, 300, 80, 3)],
            'powerups': [(2 * SCREEN_WIDTH - 200, 520)]
        },
        {
            'platforms': [(3 * gap, 560, SCREEN_WIDTH - 2 * gap, 40)],
            'enemies': [],
            'powerups': []
        },
        {
            # Collegetown level 4
            'platforms': [(4 * gap, 560, SCREEN_WIDTH - 2 * gap, 40),
                          (4 * SCREEN_WIDTH + 150, 400, 200, 20)],
            'enemies': [(4 * SCREEN_WIDTH + 300, 520, 120, 2)],
            'powerups': []
        }
    ]

    # Create groups
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    pucks = pygame.sprite.Group()
    powerups = pygame.sprite.Group()

    # Flatten world
    for idx, lvl in enumerate(levels):
        xoff = idx * SCREEN_WIDTH
        for x, y, w, h in lvl['platforms']:
            platforms.add(Platform(xoff + x, y, w, h))
        for x, y, pat, spd in lvl['enemies']:
            if idx == 2 and (x == 2 * SCREEN_WIDTH + SCREEN_WIDTH//2):
                # hockey shooter stays on rink
                enemies.add(HockeyEnemy(x, y, 100, 1))
            else:
                enemies.add(Enemy(x, y, pat, spd))
        for x, y in lvl['powerups']:
            if idx == 0:
                powerups.add(DumbbellPowerUp(xoff + x, y))
            if idx == 2:
                powerups.add(HockeyPowerUp(xoff + x, y))

    player = Player(10, 510)
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
        player.update(platforms, enemies, pucks, powerups)
        enemies.update()
        pucks.update()
        for puck in pucks:
            if pygame.sprite.spritecollide(puck, enemies, True):
                puck.kill()
        current = max(0, min(player.rect.centerx // SCREEN_WIDTH, len(levels) - 1))
        if player.rect.top > SCREEN_HEIGHT:
            show_message(screen, big_font, "Game Over", (255, 0, 0))
            break
        if player.rect.left > len(levels) * SCREEN_WIDTH:
            show_message(screen, big_font, "You Win!", (0, 255, 0))
            break
        if player.health <= 0:
            show_message(screen, big_font, "Game Over", (255, 0, 0))
            break
        cam = player.rect.centerx - SCREEN_WIDTH // 2
        cam = max(0, min(cam, len(levels) * SCREEN_WIDTH - SCREEN_WIDTH))
        screen.blit(backgrounds[current], (0, 0))
        for grp in (platforms, enemies, pucks, powerups):
            for spr in grp:
                screen.blit(spr.image, (spr.rect.x - cam, spr.rect.y))
        screen.blit(player.image, (player.rect.x - cam, player.rect.y))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
