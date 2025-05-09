import pygame
import sys

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
PUCK_LIFETIME = 60
NOTE_SPEED = 8
NOTE_LIFETIME = 60
SHOOT_COOLDOWN = 15
NOTE_COOLDOWN = 20

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
        # base
        self.base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (255,224,189), (w//2,8), 8)
        pygame.draw.rect(self.base_image, (0,0,255), (w//2-5,16,10,h-16))
        # overlays
        self.helmet = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.arc(self.helmet, (200,200,0), (w//2-12,0,24,16), 3.14,0,4)
        self.guitar = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.guitar, (160,82,45), (w//2-8,h//2-4,16,24))
        pygame.draw.rect(self.guitar, (139,69,19), (w//2+6,h//2-10,4,20))
        self.has_hockey = False
        self.has_guitar = False
        self.grown = False
        self.shoot_timer = 0
        self.note_timer = 0
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(x,y))
        self.vel = pygame.math.Vector2(0,0)
        self.on_ground = False
        self.health = 3
        self.invincible_timer = 0
        self.facing = 1
    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel.x = 0
        if keys[pygame.K_LEFT]: self.vel.x = -PLAYER_SPEED; self.facing = -1
        if keys[pygame.K_RIGHT]: self.vel.x = PLAYER_SPEED; self.facing = 1
        if keys[pygame.K_SPACE] and self.on_ground: self.vel.y = JUMP_VELOCITY
    def apply_gravity(self): self.vel.y = min(self.vel.y + GRAVITY, 15)
    def grow(self):
        if not self.grown:
            w,h = self.base_image.get_size()
            self.base_image = pygame.transform.scale(self.base_image, (w*2,h*2))
            self.grown = True
            self.rect = self.base_image.get_rect(midbottom=self.rect.midbottom)
    def lose_powerups(self):
        self.has_hockey = False
        self.has_guitar = False
        if self.grown:
            self.base_image = pygame.transform.scale(self.base_image, (30,50))
            self.grown = False
            self.rect = self.base_image.get_rect(midbottom=self.rect.midbottom)
    def update(self, platforms, enemies, pucks, notes, powerups, collectibles):
        global score
        if self.invincible_timer>0: self.invincible_timer-=1
        if self.shoot_timer>0: self.shoot_timer-=1
        if self.note_timer>0: self.note_timer-=1
        self.handle_input(); self.rect.x+=self.vel.x
        for plat in pygame.sprite.spritecollide(self,platforms,False):
            if self.vel.x>0: self.rect.right=plat.rect.left
            elif self.vel.x<0: self.rect.left=plat.rect.right
        self.apply_gravity(); self.rect.y+=self.vel.y; self.on_ground=False
        for plat in pygame.sprite.spritecollide(self,platforms,False):
            if self.vel.y>0: self.rect.bottom=plat.rect.top; self.vel.y=0; self.on_ground=True
            elif self.vel.y<0: self.rect.top=plat.rect.bottom; self.vel.y=0
        for pu in pygame.sprite.spritecollide(self,powerups,True):
            if isinstance(pu, HockeyPowerUp): self.has_hockey=True
            elif isinstance(pu, DumbbellPowerUp): self.grow()
            elif isinstance(pu, GuitarPowerUp): self.has_guitar=True
        keys = pygame.key.get_pressed()
        if self.has_hockey and keys[pygame.K_q] and self.shoot_timer<=0:
            pucks.add(Puck(self.rect.centerx, self.rect.centery, self.facing)); self.shoot_timer=SHOOT_COOLDOWN
        if self.has_guitar and keys[pygame.K_e] and self.note_timer<=0:
            notes.add(MusicNote(self.rect.centerx, self.rect.centery, self.facing)); self.note_timer=NOTE_COOLDOWN
        for en in pygame.sprite.spritecollide(self,enemies,False):
            if self.vel.y>0 and self.rect.bottom<=en.rect.top+10:
                en.kill(); self.vel.y=JUMP_VELOCITY
            elif self.invincible_timer<=0:
                self.lose_powerups(); self.health-=1; self.invincible_timer=FPS
        for col in pygame.sprite.spritecollide(self,collectibles,True): score+=1
        img = self.base_image.copy()
        if self.has_hockey: img.blit(self.helmet, (0,0))
        if self.has_guitar: img.blit(self.guitar, (0,0))
        self.image = img
class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h): super().__init__(); self.image=pygame.Surface((w,h)); self.image.fill((0,200,0)); self.rect=self.image.get_rect(topleft=(x,y))
class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y,pat,spd):
        super().__init__(); size=40; self.image=pygame.Surface((size,size)); self.image.fill((255,255,255)); pygame.draw.rect(self.image,(0,0,0),self.image.get_rect(),2)
        txt=pygame.font.Font(None,24).render("HW",True,(0,0,0)); self.image.blit(txt, txt.get_rect(center=(size//2,size//2)))
        self.rect=self.image.get_rect(topleft=(x,y)); self.start_x=x; self.range=pat; self.speed=spd; self.direction=1
    def update(self): 
      self.rect.x+=self.speed*self.direction; 
      if self.rect.x<self.start_x or self.rect.x>self.start_x+self.range: self.direction*=-1
class HockeyEnemy(Enemy):
    def __init__(self,x,y,pat,spd): super().__init__(x,y,pat,spd); self.shoot_timer=SHOOT_COOLDOWN
    def update(self): 
      super().update(); self.shoot_timer-=1; 
      if self.shoot_timer<=0: pucks.add(Puck(self.rect.centerx,self.rect.centery,self.direction)); self.shoot_timer=SHOOT_COOLDOWN
class Puck(pygame.sprite.Sprite):
    def __init__(self,x,y,d): super().__init__(); size=10; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.circle(self.image,(0,0,0),(size//2,size//2),size//2); self.rect=self.image.get_rect(center=(x,y)); self.vel=pygame.math.Vector2(PUCK_SPEED*d,0); self.lifetime=PUCK_LIFETIME
    def update(self): 
      self.rect.x+=self.vel.x; self.lifetime-=1; 
      if self.lifetime<=0: self.kill()
class MusicNote(pygame.sprite.Sprite):
    def __init__(self,x,y,d): 
      super().__init__(); size=12; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.ellipse(self.image,(0,0,0),(0,0,8,12)); pygame.draw.line(self.image,(0,0,0),(6,2),(10,-6),2)
      self.rect=self.image.get_rect(center=(x,y)); self.vel=pygame.math.Vector2(NOTE_SPEED*d,0); self.lifetime=NOTE_LIFETIME
    def update(self): 
      self.rect.x+=self.vel.x; self.lifetime-=1; 
      if self.lifetime<=0: self.kill()
class HockeyPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); size=20; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.circle(self.image,(0,0,0),(size//2,size//2),size//2); pygame.draw.circle(self.image,(255,255,255),(size//2,size//2),size//2-2); self.rect=self.image.get_rect(center=(x,y))
class DumbbellPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); size,cap=30,8; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.rect(self.image,(80,80,80),(cap,size//2-4,size-2*cap,8)); pygame.draw.circle(self.image,(80,80,80),(cap,size//2),cap); pygame.draw.circle(self.image,(80,80,80),(size-cap,size//2),cap); self.rect=self.image.get_rect(center=(x,y))
class GuitarPowerUp(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); w,h=20,20; self.image=pygame.Surface((w,h),pygame.SRCALPHA); pygame.draw.rect(self.image,(139,69,19),(5,5,10,2)); pygame.draw.circle(self.image,(160,82,45),(10,h-5),5); self.rect=self.image.get_rect(center=(x,y))
class CoinCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); size=15; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.circle(self.image,(255,223,0),(size//2,size//2),size//2); self.rect=self.image.get_rect(center=(x,y))
class SushiCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); size=16; self.image=pygame.Surface((size,size),pygame.SRCALPHA); pygame.draw.ellipse(self.image,(255,248,220),(0,4,size,8)); pygame.draw.rect(self.image, (255,69,0), (0, 2, size, 4)); self.rect=self.image.get_rect(center=(x,y))
class BeerCollectible(pygame.sprite.Sprite):
    def __init__(self,x,y): super().__init__(); w,h=12,20; self.image=pygame.Surface((w,h),pygame.SRCALPHA); pygame.draw.rect(self.image,(255,215,0),(0,4,w,h-4)); pygame.draw.rect(self.image,(255,255,255),(0,0,w,6)); self.rect=self.image.get_rect(center=(x,y))
# — Main Game Loop —
def main():
    global pucks, notes, collectibles, score
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Platformer")
    clock = pygame.time.Clock()
    font_small = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    pucks = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    collectibles = pygame.sprite.Group()
    # Load backgrounds
    try: bg_high = pygame.image.load('Images/highschool_bg.png').convert()
    except: bg_high = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_high.fill((200,200,200))
    try: bg_cornell = pygame.image.load('Images/cornell_bg.png').convert()
    except: bg_cornell = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_cornell.fill((180,50,50))
    try: bg_college = pygame.image.load('Images/collegetown_bg.png').convert()
    except: bg_college = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_college.fill((100,150,100))
    try: bg_lynah = pygame.image.load('Images/lynah_bg.png').convert()
    except: bg_lynah = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_lynah.fill((173,216,230))
    try: bg_gym = pygame.image.load('Images/gym_bg.png').convert()
    except: bg_gym = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_gym.fill((160,160,160))
    try: bg_nyc = pygame.image.load('Images/nyc_bg.png').convert()
    except: bg_nyc = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_nyc.fill((50,50,80))
    try: bg_workspace = pygame.image.load('Images/workspace_bg.png').convert()
    except: bg_workspace = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_workspace.fill((220,220,220))
    try: bg_startup = pygame.image.load('Images/startup_bg.png').convert()
    except: bg_startup = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); bg_startup.fill((240,230,140))
    backgrounds = [pygame.transform.scale(b, (SCREEN_WIDTH, SCREEN_HEIGHT)) for b in (bg_high, bg_cornell, bg_college, bg_lynah, bg_gym, bg_nyc, bg_workspace, bg_startup)]
    # Define levels including office and startup
    gap = 50
    levels = [
        {'platforms':[(0,560,SCREEN_WIDTH-gap,40),(200,450,100,20)], 'enemies':[(500,520,150,2)], 'powerups':[(300,520)], 'collectibles':[(350,500,'coin')]},
        {'platforms':[(gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies':[(900,520,100,1)], 'powerups':[], 'collectibles':[(950,500,'sushi')]},
        {'platforms':[(2*gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies':[(2*SCREEN_WIDTH+200,520,100,2)], 'powerups':[(2*SCREEN_WIDTH-200,520)], 'collectibles':[(2*SCREEN_WIDTH+350,500,'beer')]},
        {'platforms':[(3*gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies':[(3*SCREEN_WIDTH+100,520,150,3)], 'powerups':[], 'collectibles':[(3*SCREEN_WIDTH+200,500,'coin')]},
        {'platforms':[(4*gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies':[(4*SCREEN_WIDTH+300,520,120,2)], 'powerups':[(4*SCREEN_WIDTH+400,520)], 'collectibles':[(4*SCREEN_WIDTH+500,450,'sushi')]},
        {'platforms':[(5*gap,560,SCREEN_WIDTH-2*gap,40)], 'enemies':[(5*SCREEN_WIDTH+400,520,100,2),(5*SCREEN_WIDTH+600,450,80,2)], 'powerups':[], 'collectibles':[(5*SCREEN_WIDTH+350,500,'coin'),(5*SCREEN_WIDTH+450,420,'beer')]},
        # Office level
        {'platforms':[(6*gap,560,SCREEN_WIDTH-2*gap,40),(6*SCREEN_WIDTH+150,450,200,20),(6*SCREEN_WIDTH+400,350,150,20)],
         'enemies':[(6*SCREEN_WIDTH+300,520,100,1),(6*SCREEN_WIDTH+500,400,80,2)], 'powerups':[], 'collectibles':[(6*SCREEN_WIDTH+250,500,'coin'),(6*SCREEN_WIDTH+350,450,'sushi')]},
        # Startup level
        {'platforms':[(7*gap,560,SCREEN_WIDTH-2*gap,40),(7*SCREEN_WIDTH+100,460,120,20),(7*SCREEN_WIDTH+300,380,100,20)],
         'enemies':[(7*SCREEN_WIDTH+200,520,120,2),(7*SCREEN_WIDTH+450,420,100,1)], 'powerups':[], 'collectibles':[(7*SCREEN_WIDTH+150,500,'beer'),(7*SCREEN_WIDTH+350,480,'coin')]}
    ]
    # Spawn world
    for idx, lvl in enumerate(levels):
        xoff = idx * SCREEN_WIDTH
        for x,y,w,h in lvl['platforms']: platforms.add(Platform(xoff+x,y,w,h))
        for x,y,pat,spd in lvl['enemies']:
            enemies.add(Enemy(xoff+x,y,pat,spd))
            enemies.add(HockeyEnemy(xoff+x+80,y,pat,spd))
        for x,y in lvl['powerups']:
            if idx==0: powerups.add(DumbbellPowerUp(xoff+x,y))
            if idx==2: powerups.add(HockeyPowerUp(xoff+x,y))
            if idx==4: powerups.add(GuitarPowerUp(xoff+x,y))
        for x,y,t in lvl['collectibles']:
            if t=='coin': collectibles.add(CoinCollectible(xoff+x,y))
            if t=='sushi': collectibles.add(SushiCollectible(xoff+x,y))
            if t=='beer': collectibles.add(BeerCollectible(xoff+x,y))
    # Extra hockey enemies
    for i in range(len(levels)): enemies.add(HockeyEnemy(i*SCREEN_WIDTH+SCREEN_WIDTH//2,500,100,2))
    # Player
    player = Player(10,510)
    # Game loop
    running=True
    while running:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
        player.update(platforms,enemies,pucks,notes,powerups,collectibles)
        enemies.update(); pucks.update(); notes.update()
        for puck in pucks:
            if pygame.sprite.spritecollide(puck,enemies,True): puck.kill()
        for note in notes:
            if pygame.sprite.spritecollide(note,enemies,True): note.kill()
        current = max(0,min(player.rect.centerx//SCREEN_WIDTH,len(levels)-1))
        if player.rect.top>SCREEN_HEIGHT or player.health<=0:
            show_message(screen,big_font,"Game Over",(255,0,0)); break
        if player.rect.left>len(levels)*SCREEN_WIDTH:
            show_message(screen,big_font,"You Win!",(0,255,0)); break
        cam = player.rect.centerx - SCREEN_WIDTH//2
        cam = max(0,min(cam,len(levels)*SCREEN_WIDTH-SCREEN_WIDTH))
        screen.blit(backgrounds[current],(0,0))
        score_surf = font_small.render(f"Score: {score}",True,(255,255,255))
        screen.blit(score_surf,(10,10))
        for grp in (platforms,enemies,pucks,notes,powerups,collectibles):
            for spr in grp: screen.blit(spr.image,(spr.rect.x-cam,spr.rect.y))
        screen.blit(player.image,(player.rect.x-cam,player.rect.y))
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit(); sys.exit()
if __name__=='__main__': main()
