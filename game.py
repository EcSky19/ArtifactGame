import pygame
import sys

# — Constants —
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
PUCK_SPEED = 10
PUCK_LIFETIME = 60  # frames
SHOOT_COOLDOWN = 15  # frames between shots

# — Classes —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        # base image
        self.base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (255,224,189), (w//2, 8), 8)  # head
        pygame.draw.rect(self.base_image, (0,0,255), (w//2-5, 16, 10, h-16))  # body
        # helmet overlay
        self.helmet = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.arc(self.helmet, (200,200,0), (w//2-12, 0, 24, 16), 3.14, 0, 4)
        # state
        self.has_hockey = False
        self.shoot_timer = 0
        self.image = self.base_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.health = 3
        self.invincible_timer = 0
        self.facing = 1  # 1 = right, -1 = left

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

    def update(self, platforms, enemies, pucks_group, powerups_group):
        # timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        # input
        self.handle_input()
        # horizontal movement & collision
        self.rect.x += self.vel.x
        for p in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = p.rect.left
            elif self.vel.x < 0:
                self.rect.left = p.rect.right
        # gravity & vertical
        self.apply_gravity()
        self.rect.y += self.vel.y
        self.on_ground = False
        for p in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.y > 0:
                self.rect.bottom = p.rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = p.rect.bottom
                self.vel.y = 0
        # collect power-up
        if pygame.sprite.spritecollide(self, powerups_group, True):
            self.has_hockey = True
        # shooting
        keys = pygame.key.get_pressed()
        if self.has_hockey and keys[pygame.K_q] and self.shoot_timer <= 0:
            puck = Puck(self.rect.centerx, self.rect.centery, self.facing)
            pucks_group.add(puck)
            self.shoot_timer = SHOOT_COOLDOWN
        # enemy collisions: stomp or damage
        for enemy in pygame.sprite.spritecollide(self, enemies, False):
            # if falling onto enemy
            if self.vel.y > 0 and self.rect.bottom <= enemy.rect.top + 10:
                enemy.kill()
                self.vel.y = JUMP_VELOCITY
            else:
                if self.invincible_timer <= 0:
                    self.health -= 1
                    self.invincible_timer = FPS
        # update image (helmet)
        self.image = self.base_image.copy()
        if self.has_hockey:
            self.image.blit(self.helmet, (0,0))

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0, 200, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range, speed):
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
        self.range = patrol_range
        self.speed = speed
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.range:
            self.direction *= -1

class Puck(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        size = 10
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 0, 0), (size//2, size//2), size//2)
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
        pygame.draw.circle(self.image, (0, 0, 0), (size//2, size//2), size//2)
        pygame.draw.circle(self.image, (255, 255, 255), (size//2, size//2), size//2 - 2)
        self.rect = self.image.get_rect(center=(x, y))

# — Main —

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer with Hockey Power-Up")
    clock = pygame.time.Clock()

    # Load backgrounds with fallback
    try:
        bg_high = pygame.image.load('Images/highschool_bg.png').convert()
    except FileNotFoundError:
        bg_high = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_high.fill((200,200,200))
    try:
        bg_cornell = pygame.image.load('Images/cornell_bg.png').convert()
    except FileNotFoundError:
        bg_cornell = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_cornell.fill((180,50,50))
    try:
        bg_lynah = pygame.image.load('Images/lynah_bg.png').convert()
    except FileNotFoundError:
        bg_lynah = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_lynah.fill((173,216,230))
    backgrounds = [
        pygame.transform.scale(b, (SCREEN_WIDTH, SCREEN_HEIGHT)) for b in (bg_high, bg_cornell, bg_lynah)
    ]

        # Level data
    gap = 50
    levels = [
        { 'platforms': [(0,560,SCREEN_WIDTH-gap,40),(200,450,100,20),(400,350,120,20),(650,300,80,20)], 'enemies': [(500,520,150,2),(350,310,80,3)], 'powerups': [] },
        { 'platforms': [(gap,560,SCREEN_WIDTH-2*gap,40),(1000-SCREEN_WIDTH,450,100,20),(1200-SCREEN_WIDTH,350,120,20)], 'enemies': [(1100,520,100,1)], 'powerups': [] },
        { 'platforms': [(2*gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies': [], 'powerups': [(SCREEN_WIDTH*2-200,520)] }
    ]

    # Create groups
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    pucks = pygame.sprite.Group()
    powerups = pygame.sprite.Group()

    # Flatten world
    for idx, lvl in enumerate(levels):
        x_off = idx * SCREEN_WIDTH
        for x,y,w,h in lvl['platforms']:
            platforms.add(Platform(x_off+x,y,w,h))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(x_off+x,y,pat,spd))
        for x,y in lvl['powerups']:
            powerups.add(HockeyPowerUp(x_off+x,y))

    player = Player(10, 510)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update
        player.update(platforms, enemies, pucks, powerups)
        enemies.update()
        pucks.update()
        # puck-enemy collision
        for puck in pucks:
            hit = pygame.sprite.spritecollide(puck, enemies, True)
            if hit:
                puck.kill()

        # Determine current level index
        cur_level = max(0, min(player.rect.centerx // SCREEN_WIDTH, len(levels) - 1))

                # Win/Game Over
        # falling off bottom kills player
        if player.rect.top > SCREEN_HEIGHT:
            print("Game Over")
            running = False
        if player.rect.left > len(levels) * SCREEN_WIDTH:
            print("You Win!")
            running = False
        if player.health <= 0:
            print("Game Over")
            running = False

        # Camera follow
        cam_x = player.rect.centerx - SCREEN_WIDTH // 2
        max_cam = len(levels) * SCREEN_WIDTH - SCREEN_WIDTH
        cam_x = max(0, min(cam_x, max_cam))

        # Draw
        screen.blit(backgrounds[cur_level], (0, 0))
        for group in (platforms, enemies, pucks, powerups):
            for spr in group:
                screen.blit(spr.image, (spr.rect.x - cam_x, spr.rect.y))
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
