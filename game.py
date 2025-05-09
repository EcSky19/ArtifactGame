import pygame
import sys
import random

# Global groups and score
global pucks, notes, collectibles, score
pucks = None
notes = None
collectibles = None
score = 0

# — Constants —
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_VELOCITY = -12
PUCK_SPEED = 10
PUCK_LIFETIME = 30
NOTE_SPEED = 8
NOTE_LIFETIME = 60
SHOOT_COOLDOWN = 60
NOTE_COOLDOWN = 20
LEVEL_WIDTH = SCREEN_WIDTH + 100
LEVEL_MSG_DURATION = FPS * 2
LEVEL_MESSAGES = [
    "Back to High School!",
    "Welcome to Cornell!",
    "To Breazzano",
    "Hockey at Lynah",
    "Gym Time",
    "Starting To Work",
    "Start My Own Venture",
    "Time to Ship My Startup"
]

# — Utility Functions —
def show_message(screen, font, text, color):
    screen.fill((0, 0, 0))
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(surf, rect)
    pygame.display.flip()
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                waiting = False

# — Sprite Classes —
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 30, 50
        self.spawn = (x, y)
        self.base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (255,224,189), (w//2,8), 8)
        pygame.draw.rect(self.base_image, (0,0,255), (w//2-5,16,10,h-16))
        self.helmet = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.arc(self.helmet, (200,200,0), (w//2-12,0,24,16), 3.14,0,4)
        self.guitar = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.guitar, (160,82,45), (w//2-8,h//2-4,16,24))
        pygame.draw.rect(self.guitar, (139,69,19), (w//2+6,h//2-10,4,20))
        self.has_hockey = False
        self.has_guitar = False
        self.has_laptop = False
        self.max_jumps = 1
        self.jumps = 0
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(x,y))
        self.vel = pygame.math.Vector2(0,0)
        self.on_ground = False
        self.health = 3
        self.invincible_timer = 0
        self.shoot_timer = 0
        self.note_timer = 0
        self.facing = 1

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        if keys[pygame.K_LEFT]: self.vel.x = -PLAYER_SPEED; self.facing = -1
        if keys[pygame.K_RIGHT]: self.vel.x = PLAYER_SPEED; self.facing = 1
        if keys[pygame.K_SPACE]:
            if self.on_ground or self.jumps < self.max_jumps:
                self.vel.y = JUMP_VELOCITY; self.jumps += 1

    def apply_gravity(self):
        self.vel.y = min(self.vel.y + GRAVITY, 15)

    def lose_powerups(self):
        self.has_hockey = False
        self.has_guitar = False
        self.max_jumps = 1

    def update(self, platforms, enemies, pucks, notes, powerups, collectibles):
        global score
        # timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.note_timer > 0:
            self.note_timer -= 1
        # movement
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
        if self.on_ground:
            self.jumps = 0
        # power-up pickup
        for pu in pygame.sprite.spritecollide(self, powerups, True):
            if isinstance(pu, HockeyPowerUp):
                self.has_hockey = True
            elif isinstance(pu, GuitarPowerUp):
                self.has_guitar = True
            elif isinstance(pu, LaptopPowerUp):
                self.has_laptop = True
                self.max_jumps = 2
            elif isinstance(pu, GameControllerPowerUp):
                self.health += 2
        # shooting with hockey power-up
        keys = pygame.key.get_pressed()
        if self.has_hockey and keys[pygame.K_q] and self.shoot_timer <= 0:
            pucks.add(Puck(self.rect.centerx, self.rect.centery, self.facing))
            self.shoot_timer = SHOOT_COOLDOWN
        # collide enemies
        for en in pygame.sprite.spritecollide(self, enemies, False):
            if self.vel.y > 0 and self.rect.bottom <= en.rect.top + 10:
                en.kill()
                self.vel.y = JUMP_VELOCITY
            elif self.invincible_timer <= 0:
                self.lose_powerups()
                self.health -= 1
                self.invincible_timer = FPS
        # collide pucks
        for pk in pygame.sprite.spritecollide(self, pucks, True):
            if self.invincible_timer <= 0:
                self.lose_powerups()
                self.health -= 1
                self.invincible_timer = FPS
        # falling off stage
        if self.rect.top > SCREEN_HEIGHT:
            if self.invincible_timer <= 0:
                self.lose_powerups()
                self.health -= 1
                self.invincible_timer = FPS
            self.rect.topleft = self.spawn
            self.vel = pygame.math.Vector2(0, 0)
        # score collectibles
        for col in pygame.sprite.spritecollide(self, collectibles, True):
            score += 1
        # update image overlay
        img = self.base_image.copy()
        if self.has_hockey:
            img.blit(self.helmet, (0, 0))
        if self.has_guitar:
            img.blit(self.guitar, (0, 0))
        self.image = img

class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h):
        super().__init__(); self.image=pygame.Surface((w,h)); self.image.fill((0,200,0)); self.rect=self.image.get_rect(topleft=(x,y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y,pat,spd):
        super().__init__(); size=40; self.image=pygame.Surface((size,size)); self.image.fill((255,255,255)); pygame.draw.rect(self.image,(0,0,0),self.image.get_rect(),2)
        txt=pygame.font.Font(None,24).render("HW",True,(0,0,0)); self.image.blit(txt,txt.get_rect(center=(size//2,size//2)))
        self.rect=self.image.get_rect(topleft=(x,y)); self.start_x=x; self.range=pat; self.speed=spd; self.direction=1
    def update(self):
        self.rect.x+=self.speed*self.direction
        if self.rect.x<self.start_x or self.rect.x>self.start_x+self.range: self.direction*=-1

class HockeyEnemy(Enemy):
    def __init__(self,x,y,pat,spd):
        super().__init__(x,y,pat,spd)
        self.shoot_timer=SHOOT_COOLDOWN
        # red-shirt person graphic
        size = 40
        self.image = pygame.Surface((size,size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,224,189), (size//2,8), 8)
        pygame.draw.rect(self.image, (200,0,0), (size//2-10,16,20,size-16))
        self.rect = self.image.get_rect(topleft=(x,y))
    def update(self):
        super().update(); self.shoot_timer-=1
        if self.shoot_timer<=0: pucks.add(Puck(self.rect.centerx,self.rect.centery,self.direction)); self.shoot_timer=SHOOT_COOLDOWN

class Puck(pygame.sprite.Sprite):
    def __init__(self,x,y,d):
        super().__init__(); size=10; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
        pygame.draw.circle(self.image,(0,0,0),(size//2,size//2),size//2)
        self.rect=self.image.get_rect(center=(x,y)); self.vel=pygame.math.Vector2(PUCK_SPEED*d,0); self.lifetime=PUCK_LIFETIME
    def update(self): 
        self.rect.x+=self.vel.x; self.lifetime-=1; 
        if self.lifetime<=0: self.kill()

class MusicNote(pygame.sprite.Sprite):
    def __init__(self,x,y,d):
        super().__init__(); size=12; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
        pygame.draw.ellipse(self.image,(0,0,0),(0,0,8,12)); pygame.draw.line(self.image,(0,0,0),(6,2),(10,-6),2)
        self.rect=self.image.get_rect(center=(x,y)); self.vel=pygame.math.Vector2(NOTE_SPEED*d,0); self.lifetime=NOTE_LIFETIME
    def update(self):
        self.rect.x+=self.vel.x; self.lifetime-=1
        if self.lifetime<=0: self.kill()

class GameControllerPowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 24
        # simple controller icon: gray rectangle + two circles as “buttons”
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # body
        pygame.draw.rect(self.image, (100,100,100), (0, size*0.3, size, size*0.4), border_radius=6)
        # left button
        pygame.draw.circle(self.image, (200,0,0), (int(size*0.3), int(size*0.5)), 4)
        # right button
        pygame.draw.circle(self.image, (0,200,0), (int(size*0.7), int(size*0.5)), 4)
        self.rect = self.image.get_rect(center=(x, y))

class HockeyPowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 20
        # black puck icon
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            self.image,
            (0, 0, 0),                  # solid black
            (size // 2, size // 2),     # center
            size // 2                   # radius
        )
        self.rect = self.image.get_rect(center=(x, y))

class DumbbellPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): 
      super().__init__(); size,cap=30,8; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
      pygame.draw.rect(self.image,(80,80,80),(cap,size//2-4,size-2*cap,8)); pygame.draw.circle(self.image,(80,80,80),(cap,size//2),cap)
      pygame.draw.circle(self.image,(80,80,80),(size-cap,size//2),cap); self.rect=self.image.get_rect(center=(x,y))

class GuitarPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): 
        super().__init__(); w,h=20,20; self.image=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.rect(self.image,(139,69,19),(5,5,10,2)); pygame.draw.circle(self.image,(160,82,45),(10,h-5),5)
        self.rect=self.image.get_rect(center=(x,y))

class LaptopPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): 
        super().__init__(); size=20; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
        pygame.draw.rect(self.image,(50,50,50),(0,0,size,int(size*0.6))); pygame.draw.rect(self.image,(80,80,80),(int(size*0.1),int(size*0.6),int(size*0.8),int(size*0.2)))
        self.rect=self.image.get_rect(center=(x,y))

class CoinCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__(); size=15; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
        pygame.draw.circle(self.image,(255,223,0),(size//2,size//2),size//2); self.rect=self.image.get_rect(center=(x,y))

class SushiCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__(); size=16; self.image=pygame.Surface((size,size),pygame.SRCALPHA)
        pygame.draw.ellipse(self.image,(255,248,220),(0,4,size,8)); pygame.draw.rect(self.image,(255,69,0),(0,2,size,4))
        self.rect=self.image.get_rect(center=(x,y))

class BeerCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y): 
        super().__init__(); w,h=12,20; self.image=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.rect(self.image,(255,215,0),(0,4,w,h-4)); pygame.draw.rect(self.image,(255,255,255),(0,0,w,6))
        self.rect=self.image.get_rect(center=(x,y))

# — Main Game Loop —
def main():
    global pucks, notes, collectibles, score
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer")
    clock = pygame.time.Clock()
    font_small = pygame.font.Font(None, 36)
    big_font   = pygame.font.Font(None, 72)

    platforms    = pygame.sprite.Group()
    enemies      = pygame.sprite.Group()
    pucks        = pygame.sprite.Group()
    notes        = pygame.sprite.Group()
    powerups     = pygame.sprite.Group()
    collectibles = pygame.sprite.Group()

    # Load backgrounds
    bg_names = [
        'highschool_bg', 'cornell_bg', 'collegetown_bg', 'lynah_bg',
        'gym_bg', 'nyc_bg',        'workspace_bg','startup_bg'
    ]
    backgrounds = []
    for name in bg_names:
        try:
            img = pygame.image.load(f'Images/{name}.png').convert()
        except:
            img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            img.fill((150,150,150))
        backgrounds.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))

    # Define all levels
    gap = 30
    levels = [
        # 1: High School
        {'platforms': [(0,560,SCREEN_WIDTH-gap,40), (200,450,120,10), (400,380,100,10)],
         'enemies': [(500,520,150,2), (300,480,80,1)],
         'powerups': [(300,520,'hockey'), (450,450,'laptop')],
         'collectibles': [(350,500,'coin'), (550,450,'sushi')]},
        # 2: Cornell Quad
        {'platforms': [(gap,560,SCREEN_WIDTH-2*gap,40), (150,470,100,10), (500,400,150,10)],
         'enemies': [(900,520,100,1), (700,450,120,2)],
         'powerups': [(650,420,'hockey'), (750,380,'laptop')],
         'collectibles': [(950,500,'sushi'), (550,460,'beer')]},
        # 3: Engineering College
        {'platforms': [(2*gap,560,SCREEN_WIDTH-2*gap,40), (2*SCREEN_WIDTH+250,470,120,10), (2*SCREEN_WIDTH+500,380,100,10)],
         'enemies': [(2*SCREEN_WIDTH+200,520,130,2), (2*SCREEN_WIDTH+600,430,80,1)],
         'powerups': [(2*SCREEN_WIDTH+300,500,'laptop'), (2*SCREEN_WIDTH+400,450,'hockey')],
         'collectibles': [(2*SCREEN_WIDTH+350,500,'coin'), (2*SCREEN_WIDTH+450,440,'sushi')]},
        # 4: Lynah Rink
        {'platforms': [(3*gap,560,SCREEN_WIDTH-2*gap,40), (3*SCREEN_WIDTH+100,480,140,10), (3*SCREEN_WIDTH+450,360,120,10)],
         'enemies': [(3*SCREEN_WIDTH+100,520,150,3), (3*SCREEN_WIDTH+600,430,110,2)],
         'powerups': [(3*SCREEN_WIDTH+300,500,'hockey'), (3*SCREEN_WIDTH+500,400,'laptop')],
         'collectibles': [(3*SCREEN_WIDTH+200,500,'coin'), (3*SCREEN_WIDTH+350,460,'beer')]},
        # 5: Campus Gym
        {'platforms': [(4*gap,560,SCREEN_WIDTH-2*gap,40), (4*SCREEN_WIDTH+150,470,130,10), (4*SCREEN_WIDTH+400,380,100,10)],
         'enemies': [(4*SCREEN_WIDTH+300,520,120,2), (4*SCREEN_WIDTH+700,410,100,1)],
         'powerups': [(4*SCREEN_WIDTH+400,520,'laptop'), (4*SCREEN_WIDTH+600,480,'hockey')],
         'collectibles': [(4*SCREEN_WIDTH+500,450,'sushi'), (4*SCREEN_WIDTH+650,420,'coin')]},
        # 6: NYC Street
        {'platforms': [(5*gap,560,SCREEN_WIDTH-2*gap,40), (5*SCREEN_WIDTH+200,460,140,10), (5*SCREEN_WIDTH+500,360,100,10)],
         'enemies': [(5*SCREEN_WIDTH+400,520,100,2), (5*SCREEN_WIDTH+600,450,80,2)],
         'powerups': [(5*SCREEN_WIDTH+500,500,'hockey'), (5*SCREEN_WIDTH+650,450,'laptop')],
         'collectibles': [(5*SCREEN_WIDTH+350,500,'beer'), (5*SCREEN_WIDTH+450,420,'coin')]},
        # 7: Dev Workspace
        {'platforms': [(6*gap,560,SCREEN_WIDTH-2*gap,40), (6*SCREEN_WIDTH+150,450,200,20), (6*SCREEN_WIDTH+400,350,150,20)],
         'enemies': [(6*SCREEN_WIDTH+300,520,100,1), (6*SCREEN_WIDTH+500,400,80,2)],
         'powerups': [(6*SCREEN_WIDTH+250,500,'laptop'), (6*SCREEN_WIDTH+550,450,'hockey')],
         'collectibles': [(6*SCREEN_WIDTH+250,500,'coin'), (6*SCREEN_WIDTH+350,450,'sushi')]},
        # 8: Startup Launch
        {'platforms': [(7*gap,560,SCREEN_WIDTH-2*gap,40), (7*SCREEN_WIDTH+100,460,120,20), (7*SCREEN_WIDTH+300,380,100,20)],
         'enemies': [(7*SCREEN_WIDTH+200,520,120,2), (7*SCREEN_WIDTH+450,420,100,1)],
         'powerups': [(7*SCREEN_WIDTH+350,480,'laptop'), (7*SCREEN_WIDTH+650,430,'hockey')],
         'collectibles': [(7*SCREEN_WIDTH+150,500,'beer'), (7*SCREEN_WIDTH+350,480,'coin')]}
    ]

    # spawn
    for idx, lvl in enumerate(levels):
        xoff = idx * LEVEL_WIDTH
        for x,y,w,h in lvl['platforms']:
            platforms.add(Platform(xoff+x,y,w,h))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(xoff+x,y,pat,spd))
            enemies.add(HockeyEnemy(xoff+x+80,y,pat,spd))
        for x,y,t in lvl['powerups']:
            if t=='hockey': powerups.add(HockeyPowerUp(xoff+x,y))
            if t=='laptop': powerups.add(LaptopPowerUp(xoff+x,y))
            if t == 'controller':powerups.add(GameControllerPowerUp(xoff + x, y))
        for x,y,c in lvl['collectibles']:
            if c=='coin': collectibles.add(CoinCollectible(xoff+x,y))
            if c=='sushi': collectibles.add(SushiCollectible(xoff+x,y))
            if c=='beer': collectibles.add(BeerCollectible(xoff+x,y))
    for idx in range(len(levels)):
      xoff = idx * LEVEL_WIDTH
      level_left  = xoff + 50
      level_right = xoff + LEVEL_WIDTH - 50
      level_top   = 100
      level_bottom= SCREEN_HEIGHT - 100
      # spawn 3 extra random power‑ups per level
      for _ in range(3):
        pu_type = random.choice(['hockey', 'laptop', 'controller'])
        x = random.randint(level_left, level_right)
        y = random.randint(level_top, level_bottom)
        if pu_type == 'hockey':
            powerups.add(HockeyPowerUp(x, y))
        elif pu_type == 'laptop':
            powerups.add(LaptopPowerUp(x, y))
        else:
            powerups.add(GameControllerPowerUp(x, y))

      # spawn 8 extra random collectibles per level
      for _ in range(8):
        col_type = random.choice(['coin', 'sushi', 'beer'])
        x = random.randint(level_left, level_right)
        y = random.randint(level_top, level_bottom)
        if col_type == 'coin':
            collectibles.add(CoinCollectible(x, y))
        elif col_type == 'sushi':
            collectibles.add(SushiCollectible(x, y))
        else:
            collectibles.add(BeerCollectible(x, y))

    # spawn with per‑level difficulty scaling
    for idx, lvl in enumerate(levels):
        xoff = idx * SCREEN_WIDTH

        # increase difficulty by 10% per level index
        diff = 1 + idx * 0.1

        # shrink platforms slightly
        for x, y, w, h in lvl['platforms']:
            adj_w = max(50, int(w - idx * 10))
            platforms.add(Platform(xoff + x, y, adj_w, h))

        # speed up enemies and lengthen their patrol
        for x, y, pat, spd in lvl['enemies']:
            scaled_spd = max(1, int(spd * diff))
            scaled_pat = int(pat * diff)
            enemies.add(Enemy(xoff + x, y, scaled_pat, scaled_spd))
            enemies.add(HockeyEnemy(xoff + x + 80, y, scaled_pat, scaled_spd))

        # power‑ups & collectibles unchanged
        for x, y, t in lvl['powerups']:
            if t == 'hockey': powerups.add(HockeyPowerUp(xoff + x, y))
            if t == 'laptop': powerups.add(LaptopPowerUp(xoff + x, y))
        for x, y, c in lvl['collectibles']:
            if c == 'coin':  collectibles.add(CoinCollectible(xoff + x, y))
            if c == 'sushi': collectibles.add(SushiCollectible(xoff + x, y))
            if c == 'beer':  collectibles.add(BeerCollectible(xoff + x, y))

    player  = Player(10, 510)
    last_level    = -1
    level_msg_tmr = 0
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_q:
               # only if we've picked up the hockey power‑up and cooldown is over
               if player.has_hockey and player.shoot_timer <= 0:
                   pucks.add(Puck(
                       player.rect.centerx,
                       player.rect.centery,
                       player.facing
                   ))
                   player.shoot_timer = SHOOT_COOLDOWN

        # update all sprites
        player.update(platforms, enemies, pucks, notes, powerups, collectibles)
        enemies.update()
        pucks.update()
        notes.update()

        # ── GAME OVER WHEN HEALTH REACHES ZERO ──
        if player.health <= 0:
            show_message(screen, big_font, "Game Over", (255, 0, 0))
            running = False
            continue

        # camera
        cam = player.rect.centerx - SCREEN_WIDTH // 2
        cam = max(0, min(cam, len(levels)*LEVEL_WIDTH - SCREEN_WIDTH))

        # draw background
        current_level = cam // LEVEL_WIDTH
        # ── detect level change ──
        if current_level != last_level:
            last_level    = current_level
            level_msg_tmr = LEVEL_MSG_DURATION
        screen.blit(backgrounds[current_level], (0, 0))

        # ── HEALTH DISPLAY ──
        health_surf = font_small.render(f"Health: {player.health}", True, (255, 0, 0))
        screen.blit(health_surf, (10, 10))

        # ── SCORE DISPLAY ──
        score_surf = font_small.render(f"Score: {score}", True, (255, 215, 0))
        # position at top‑right, with a 10px margin
        score_x   = SCREEN_WIDTH - score_surf.get_width() - 10
        screen.blit(score_surf, (score_x, 10))

        # ── LEVEL BANNER ──
        if level_msg_tmr > 0:
            # center message text
            text = LEVEL_MESSAGES[current_level]
            msg_surf = font_small.render(text, True, (255, 255, 255))
            msg_x = (SCREEN_WIDTH - msg_surf.get_width()) // 2
            screen.blit(msg_surf, (msg_x, 50))
            level_msg_tmr -= 1

        # draw all sprites
        for grp in (platforms, enemies, pucks, notes, powerups, collectibles):
            for spr in grp:
                screen.blit(spr.image, (spr.rect.x - cam, spr.rect.y))
        screen.blit(player.image, (player.rect.x - cam, player.rect.y))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__=='__main__':
    main()