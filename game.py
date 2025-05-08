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
        if keys[pygame.K_SPACE] and self.on_ground: self.vel.y = -12

    def apply_gravity(self):
        self.vel.y = min(self.vel.y + GRAVITY, 15)

    def update(self, platforms, enemies, doors, current_level):
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
        # Enemy collision
        if pygame.sprite.spritecollide(self, enemies, False) and self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = FPS
        # Door collision
        hits = pygame.sprite.spritecollide(self, doors, False)
        for door in hits:
            if door.level == current_level:
                # teleport to next level start
                next_level = current_level + 1
                if next_level < len(doors.levels):
                    self.rect.x = next_level * SCREEN_WIDTH + 10
                    self.vel = pygame.math.Vector2(0,0)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h):
        super().__init__(); self.image = pygame.Surface((w,h)); self.image.fill((0,200,0)); self.rect = self.image.get_rect(topleft=(x,y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x,y,patrol,spd):
        super().__init__(); s=40; self.image=pygame.Surface((s,s)); self.image.fill((255,255,255)); pygame.draw.rect(self.image,(0,0,0),self.image.get_rect(),2)
        f=pygame.font.Font(None,24); t = f.render("HW",True,(0,0,0)); self.image.blit(t,t.get_rect(center=(s//2,s//2)))
        self.rect=self.image.get_rect(topleft=(x,y)); self.start_x=x; self.range=patrol; self.spd=spd; self.dir=1
    def update(self):
        self.rect.x += self.spd*self.dir
        if self.rect.x < self.start_x or self.rect.x > self.start_x+self.range: self.dir*=-1

class Door(pygame.sprite.Sprite):
    levels = []  # placeholder for number of levels
    def __init__(self, x, y, level):
        super().__init__()
        self.image = pygame.Surface((40,60))
        self.image.fill((139,69,19))  # brown door
        pygame.draw.rect(self.image, (160,82,45), (5,5,30,50))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.level = level

# — Main —
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pygame.time.Clock()
        # Load backgrounds (with fallback if files missing)
    try:
        bg_high = pygame.image.load('Images/highschool_bg.png').convert()
    except FileNotFoundError:
        # solid color fallback
        bg_high = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_high.fill((200, 200, 200))  # light grey school hallway
    try:
        bg_cornell = pygame.image.load('Images/cornell_bg.png').convert()
    except FileNotFoundError:
        bg_cornell = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_cornell.fill((180, 50, 50))  # Cornell red
    backgrounds = [
        pygame.transform.scale(bg_high, (SCREEN_WIDTH, SCREEN_HEIGHT)),
        pygame.transform.scale(bg_cornell, (SCREEN_WIDTH, SCREEN_HEIGHT))
    ]

# Level definitions
    levels = [
        { 'platforms': [(0,560,800,40),(200,450,100,20),(400,350,120,20),(650,300,80,20)], 'enemies': [(500,520,150,2)], 'door_y':500 },
        { 'platforms': [(800,560,800,40),(1000,450,100,20),(1200,350,120,20)], 'enemies': [(1100,520,100,1)], 'door_y':500 }
    ]
    # Create groups
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    # Flatten world
    for idx, lvl in enumerate(levels):
        x_off = idx * SCREEN_WIDTH
        for x,y,w,h in lvl['platforms']:
            platforms.add(Platform(x_off + x, y, w, h))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(x_off + x, y, pat, spd))
        # door at end of level
        d_x = x_off + SCREEN_WIDTH - 50
        d_y = lvl['door_y']
        door = Door(d_x, d_y, idx)
        doors.add(door)
    Door.levels = levels  # store for access

    player = Player(10, 510)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
        # calculate current level
        cur_level = player.rect.centerx // SCREEN_WIDTH
        # update
        player.update(platforms, enemies, doors, cur_level)
        enemies.update()
        # check win
        if cur_level >= len(levels):
            # show win
            running = False
        # camera
        cam_x = int(player.rect.centerx - SCREEN_WIDTH/2)
        cam_x = max(0, min(cam_x, len(levels)*SCREEN_WIDTH - SCREEN_WIDTH))
        # draw bg
        screen.blit(backgrounds[cur_level], (0,0))
        # draw sprites
        for g in (platforms, enemies, doors):
            for spr in g:
                screen.blit(spr.image, (spr.rect.x - cam_x, spr.rect.y))
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y))
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit(); sys.exit()

if __name__=='__main__': main()
