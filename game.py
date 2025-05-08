import pygame
import sys

# — Constants —
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12

# — Classes —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        self.original_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, (255,224,189), (w//2, 8), 8)  # head
        pygame.draw.rect(self.original_image, (0,0,255), (w//2-5, 16, 10, h-16))  # body
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.math.Vector2(0,0)
        self.on_ground = False
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

    def update(self, platforms, enemies):
        # invincibility timer
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        # input and movement
        self.handle_input()
        self.rect.x += self.vel.x
        for p in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = p.rect.left
            elif self.vel.x < 0:
                self.rect.left = p.rect.right
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
        # enemy collision
        if pygame.sprite.spritecollide(self, enemies, False) and self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = FPS

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0,200,0))
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range, speed):
        super().__init__()
        size = 40
        self.image = pygame.Surface((size, size))
        self.image.fill((255,255,255))
        pygame.draw.rect(self.image, (0,0,0), self.image.get_rect(), 2)
        font = pygame.font.Font(None, 24)
        txt = font.render("HW", True, (0,0,0))
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

# — Main —
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer - High School to Cornell")
    clock = pygame.time.Clock()

    # load backgrounds with fallback
    try:
        bg_high = pygame.image.load('Images/highschool_bg.png').convert()
    except FileNotFoundError:
        bg_high = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_high.fill((200, 200, 200))
    try:
        bg_cornell = pygame.image.load('Images/cornell_bg.png').convert()
    except FileNotFoundError:
        bg_cornell = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_cornell.fill((180, 50, 50))
    backgrounds = [pygame.transform.scale(bg_high, (SCREEN_WIDTH, SCREEN_HEIGHT)),
                   pygame.transform.scale(bg_cornell, (SCREEN_WIDTH, SCREEN_HEIGHT))]

    # level data
    levels = [
        { 'platforms': [(0,560,1000,40),(200,450,100,20),(400,350,120,20),(650,300,80,20)],
          'enemies': [(500,520,150,2),(350,310,80,3)] },
        { 'platforms': [(800,560,1000,40),(1000,450,100,20),(1200,350,120,20)],
          'enemies': [(1100,520,100,1)] }
    ]

    # create sprite groups
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    # flatten world
    for idx, lvl in enumerate(levels):
        x_off = idx * SCREEN_WIDTH
        for x,y,w,h in lvl['platforms']:
            platforms.add(Platform(x_off + x, y, w, h))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(x_off + x, y, pat, spd))

    # player
    player = Player(10, 510)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # update
        player.update(platforms, enemies)
        enemies.update()

        # determine current level for background
        cur_level = player.rect.centerx // SCREEN_WIDTH
        cur_level = max(0, min(cur_level, len(levels)-1))

        # win condition when passing last screen
        if player.rect.left > len(levels)*SCREEN_WIDTH:
            print("You Win!")
            running = False

        # game over
        if player.health <= 0:
            print("Game Over")
            running = False

        # camera follow
        cam_x = player.rect.centerx - SCREEN_WIDTH // 2
        cam_x = max(0, min(cam_x, len(levels)*SCREEN_WIDTH - SCREEN_WIDTH))

        # draw
        screen.blit(backgrounds[cur_level], (0,0))
        for spr in platforms:
            screen.blit(spr.image, (spr.rect.x - cam_x, spr.rect.y))
        for spr in enemies:
            screen.blit(spr.image, (spr.rect.x - cam_x, spr.rect.y))
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
