import pygame
import sys

# — Constants —
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
BG_COLOR = (135, 206, 235)

# — Player Sprite —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        self.original_image = pygame.Surface((w, h), pygame.SRCALPHA)
        head_radius = 8
        pygame.draw.circle(self.original_image, (255,224,189), (w//2, head_radius), head_radius)
        body_rect = pygame.Rect(w//2-5, head_radius*2, 10, h-head_radius*2)
        pygame.draw.rect(self.original_image, (0,0,255), body_rect)
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.math.Vector2(0,0)
        self.on_ground = False
        self.grown = False
        self.health = 3
        self.invincible_timer = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        if keys[pygame.K_LEFT]: self.vel.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]: self.vel.x = PLAYER_SPEED
        if keys[pygame.K_SPACE] and self.on_ground: self.vel.y = JUMP_VELOCITY

    def apply_gravity(self):
        self.vel.y = min(self.vel.y + GRAVITY, 15)

    def grow(self):
        if not self.grown:
            w, h = self.original_image.get_size()
            self.image = pygame.transform.scale(self.original_image, (w*2, h*2))
            mid = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom=mid)
            self.grown = True

    def shrink(self):
        if self.grown:
            mid = self.rect.midbottom
            self.image = self.original_image
            self.rect = self.image.get_rect(midbottom=mid)
            self.grown = False

    def take_damage(self):
        if self.invincible_timer <= 0:
            if self.grown: self.shrink()
            self.health -= 1
            self.invincible_timer = FPS

    def update(self, platforms, powerups, enemies):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        self.handle_input()
        self.rect.x += self.vel.x
        for p in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0: self.rect.right = p.rect.left
            elif self.vel.x < 0: self.rect.left = p.rect.right
        self.apply_gravity()
        self.rect.y += self.vel.y
        self.on_ground = False
        for p in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.y > 0:
                self.rect.bottom = p.rect.top; self.vel.y = 0; self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = p.rect.bottom; self.vel.y = 0
        if pygame.sprite.spritecollide(self, powerups, True): self.grow()
        if pygame.sprite.spritecollide(self, enemies, False): self.take_damage()

# — Static Sprites —
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(); self.image = pygame.Surface((w,h)); self.image.fill((0,255,0)); self.rect = self.image.get_rect(topleft=(x,y))

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); s = 30; self.image = pygame.Surface((s,s), pygame.SRCALPHA)
        c = 8; pygame.draw.rect(self.image, (80,80,80), (c, s//2-4, s-2*c, 8))
        pygame.draw.circle(self.image, (80,80,80), (c, s//2), c)
        pygame.draw.circle(self.image, (80,80,80), (s-c, s//2), c)
        self.rect = self.image.get_rect(center=(x,y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol, speed):
        super().__init__(); s = 40; self.image = pygame.Surface((s,s)); self.image.fill((255,255,255)); pygame.draw.rect(self.image, (0,0,0), self.image.get_rect(), 2)
        f = pygame.font.Font(None, 24); t = f.render("HW", True, (0,0,0)); self.image.blit(t, t.get_rect(center=(s//2,s//2)))
        self.rect = self.image.get_rect(topleft=(x,y)); self.start_x = x; self.range = patrol; self.speed = speed; self.direction = 1
    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.range:
            self.direction *= -1

# — Level Data —
levels = [
    { 'platforms': [(0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40),(200,450,100,20),(400,350,120,20),(650,300,80,20)],
      'powerups': [(300,420)], 'enemies': [(500, SCREEN_HEIGHT-80,150,2),(350,310,80,3)] },
    { 'platforms': [(0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40),(150,400,100,20),(350,300,100,20)],
      'powerups': [(200,360)], 'enemies': [(250, SCREEN_HEIGHT-80,100,1)] }
]

# — Game Over & Win Screens —
def show_message(screen, font, text, color):
    screen.fill((0,0,0)); t = font.render(text, True, color)
    r = t.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)); screen.blit(t, r); pygame.display.flip()
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN: waiting = False

# — Main Loop with Camera —
def main():
    pygame.init(); screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT)); pygame.display.set_caption("Platformer with Scrolling"); clock = pygame.time.Clock()
    small_font = pygame.font.Font(None,36); big_font = pygame.font.Font(None,72)

    # Create world groups
    platforms = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    # Flatten levels into world coordinates
    for idx, lvl in enumerate(levels):
        x_offset = idx * SCREEN_WIDTH
        for x,y,w,h in lvl['platforms']:
            platforms.add(Platform(x + x_offset, y, w, h))
        for x,y in lvl['powerups']:
            powerups.add(PowerUp(x + x_offset, y))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(x + x_offset, y, pat, spd))

    total_width = len(levels) * SCREEN_WIDTH

    # Player in world
    player = Player(50, SCREEN_HEIGHT-150)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False

        player.update(platforms, powerups, enemies)
        enemies.update()

        # Check win condition
        if player.rect.right > total_width:
            show_message(screen, big_font, "You Win!", (0,255,0)); break
        # Game over
        if player.health <= 0:
            show_message(screen, big_font, "Game Over", (255,0,0)); break

        # Camera follows player (clamped)
        cam_x = player.rect.centerx - SCREEN_WIDTH // 2
        cam_x = max(0, min(cam_x, total_width - SCREEN_WIDTH))

        # Draw
        screen.fill(BG_COLOR)
        for sprite in platforms:
            screen.blit(sprite.image, (sprite.rect.x - cam_x, sprite.rect.y))
        for sprite in powerups:
            screen.blit(sprite.image, (sprite.rect.x - cam_x, sprite.rect.y))
        for sprite in enemies:
            screen.blit(sprite.image, (sprite.rect.x - cam_x, sprite.rect.y))
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y))
        screen.blit(small_font.render(f"Health: {player.health}", True, (255,0,0)), (10,10))
        pygame.display.flip(); clock.tick(FPS)

    pygame.quit(); sys.exit()

if __name__ == "__main__": main()
