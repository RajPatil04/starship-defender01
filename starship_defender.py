#!/usr/bin/env python3
"""
Starship Defender - A space shooter game created with Pygame
"""
import pygame
import random
import os
import sys
import math
from enum import Enum

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Starship Defender")
clock = pygame.time.Clock()

# Create assets directory if it doesn't exist
if not os.path.exists('assets'):
    os.makedirs('assets')
    os.makedirs('assets/sounds')
    os.makedirs('assets/images')

# Load images (using simple shapes for now)
def draw_player_ship(surface, color=BLUE, width=30, height=40):
    """Draw a simple player ship"""
    ship = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.polygon(ship, color, [(width//2, 0), (0, height), (width, height)])
    pygame.draw.polygon(ship, WHITE, [(width//2, 0), (0, height), (width, height)], 1)
    return ship

def draw_enemy_ship1(surface, color=RED, width=30, height=30):
    """Draw a simple enemy ship type 1"""
    ship = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.polygon(ship, color, [(0, 0), (width, 0), (width//2, height)])
    pygame.draw.polygon(ship, WHITE, [(0, 0), (width, 0), (width//2, height)], 1)
    return ship

def draw_enemy_ship2(surface, color=GREEN, width=40, height=20):
    """Draw a simple enemy ship type 2"""
    ship = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(ship, color, (0, 0, width, height))
    pygame.draw.ellipse(ship, WHITE, (0, 0, width, height), 1)
    return ship

def draw_bullet(surface, color=YELLOW, width=4, height=10):
    """Draw a simple bullet"""
    bullet = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(bullet, color, (0, 0, width, height))
    return bullet

def draw_explosion(surface, radius, color=YELLOW):
    """Draw a simple explosion"""
    explosion = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(explosion, color, (radius, radius), radius)
    return explosion

# Load game assets
player_img = draw_player_ship(screen)
enemy_img1 = draw_enemy_ship1(screen)
enemy_img2 = draw_enemy_ship2(screen)
bullet_img = draw_bullet(screen)
player_bullet_img = draw_bullet(screen, BLUE)
enemy_bullet_img = draw_bullet(screen, RED)

# Create stars for background
stars = []
for i in range(100):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    speed = random.uniform(0.1, 0.5)
    size = random.randint(1, 3)
    stars.append([x, y, speed, size])

# Define PowerUp types
class PowerUpType(Enum):
    SHIELD = 1
    DOUBLE_SHOT = 2
    RAPID_FIRE = 3

# Game classes
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speedx = 0
        self.lives = 3
        self.score = 0
        self.shoot_delay = 250  # milliseconds
        self.last_shot = pygame.time.get_ticks()
        self.shield = 0  # Shield duration in milliseconds
        self.double_shot = False
        self.rapid_fire = False
        self.power_up_end_time = {
            PowerUpType.SHIELD: 0,
            PowerUpType.DOUBLE_SHOT: 0,
            PowerUpType.RAPID_FIRE: 0
        }
        self.hidden = False
        self.hide_timer = 0

    def update(self):
        # Check if power-ups have expired
        current_time = pygame.time.get_ticks()
        
        # Shield check
        if self.power_up_end_time[PowerUpType.SHIELD] < current_time:
            self.shield = 0
            
        # Double shot check
        if self.power_up_end_time[PowerUpType.DOUBLE_SHOT] < current_time:
            self.double_shot = False
            
        # Rapid fire check
        if self.power_up_end_time[PowerUpType.RAPID_FIRE] < current_time:
            self.rapid_fire = False
            self.shoot_delay = 250  # Reset to normal fire rate
        
        # Unhide if hidden
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2
            self.rect.bottom = SCREEN_HEIGHT - 10

        # Movement
        self.speedx = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -8
        if keystate[pygame.K_RIGHT]:
            self.speedx = 8
        
        # Update position
        self.rect.x += self.speedx
        
        # Keep player on screen
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and not self.hidden:
            self.last_shot = now
            if self.double_shot:
                bullet1 = Bullet(self.rect.left + 5, self.rect.top, -10, player_bullet_img, True)
                bullet2 = Bullet(self.rect.right - 5, self.rect.top, -10, player_bullet_img, True)
                all_sprites.add(bullet1, bullet2)
                bullets.add(bullet1, bullet2)
                if shoot_sound:
                    shoot_sound.play()
            else:
                bullet = Bullet(self.rect.centerx, self.rect.top, -10, player_bullet_img, True)
                all_sprites.add(bullet)
                bullets.add(bullet)
                if shoot_sound:
                    shoot_sound.play()

    def hide(self):
        """Hide the player temporarily when hit"""
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT + 200)

    def apply_powerup(self, powerup_type):
        """Apply power-up effects to the player"""
        duration = 5000  # 5 seconds for all power-ups
        current_time = pygame.time.get_ticks()
        
        if powerup_type == PowerUpType.SHIELD:
            self.shield = 1
            self.power_up_end_time[PowerUpType.SHIELD] = current_time + duration
            
        elif powerup_type == PowerUpType.DOUBLE_SHOT:
            self.double_shot = True
            self.power_up_end_time[PowerUpType.DOUBLE_SHOT] = current_time + duration
            
        elif powerup_type == PowerUpType.RAPID_FIRE:
            self.rapid_fire = True
            self.shoot_delay = 100  # Faster firing rate
            self.power_up_end_time[PowerUpType.RAPID_FIRE] = current_time + duration

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type=1):
        pygame.sprite.Sprite.__init__(self)
        self.enemy_type = enemy_type
        
        if enemy_type == 1:
            self.image = enemy_img1
            self.speed_y = random.randrange(1, 3)
            self.speed_x = random.randrange(-1, 2)
            self.shoot_chance = 0.005  # 0.5% chance to shoot per frame
            self.health = 1
            self.score_value = 10
        else:  # enemy_type == 2
            self.image = enemy_img2
            self.speed_y = random.randrange(1, 2)
            self.speed_x = random.randrange(-2, 3)
            self.shoot_chance = 0.01  # 1% chance to shoot per frame
            self.health = 2
            self.score_value = 20
            
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = random.randrange(1000, 3000)

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        
        # Bounce off the edges
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.speed_x = -self.speed_x
            
        # If enemy goes off the bottom of the screen, respawn at the top
        if self.rect.top > SCREEN_HEIGHT + 10:
            self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speed_y = random.randrange(1, 3)
            
        # Random shooting
        if random.random() < self.shoot_chance:
            self.shoot()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.bottom, 5, enemy_bullet_img, False)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, img, is_player_bullet):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = speed
        self.is_player_bullet = is_player_bullet

    def update(self):
        self.rect.y += self.speedy
        # Remove if it goes off screen
        if self.is_player_bullet:
            if self.rect.bottom < 0:
                self.kill()
        else:
            if self.rect.top > SCREEN_HEIGHT:
                self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.frame = 0
        self.image = draw_explosion(screen, self.size * (self.frame + 1))
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame_rate = 50
        self.last_update = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame < 8:  # 8 frames of explosion
                self.image = draw_explosion(screen, self.size * (8 - self.frame) / 2)
                self.rect = self.image.get_rect()
                self.rect.center = self.rect.center
            else:
                self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(list(PowerUpType))
        
        # Create a simple colored circle for the power-up
        size = 20
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if self.type == PowerUpType.SHIELD:
            color = BLUE
        elif self.type == PowerUpType.DOUBLE_SHOT:
            color = GREEN
        else:  # RAPID_FIRE
            color = YELLOW
            
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        pygame.draw.circle(self.image, WHITE, (size//2, size//2), size//2, 1)
        
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 2

    def update(self):
        self.rect.y += self.speedy
        # Kill if it moves off the bottom of the screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Game state management
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# Initialize game state
game_state = GameState.MENU
difficulty_timer = 0
difficulty_level = 1
spawn_rate = 0.02  # Initial enemy spawn rate

# Initialize sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Load sounds
shoot_sound = None
explosion_sound = None
powerup_sound = None
game_over_sound = None
background_music = None

try:
    # Create simple sound files if they don't exist
    shoot_sound = pygame.mixer.Sound('assets/sounds/laser.wav')
    explosion_sound = pygame.mixer.Sound('assets/sounds/explosion.wav')
    powerup_sound = pygame.mixer.Sound('assets/sounds/powerup.wav')
    game_over_sound = pygame.mixer.Sound('assets/sounds/gameover.wav')
    
    # Set volume
    shoot_sound.set_volume(0.3)
    explosion_sound.set_volume(0.5)
    powerup_sound.set_volume(0.5)
    game_over_sound.set_volume(0.7)
    
    # Load and play background music
    pygame.mixer.music.load('assets/sounds/background.wav')
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(loops=-1)
except:
    print("Warning: Sound files not found. Game will run without sound.")

# Game functions
def draw_text(surf, text, size, x, y, color=WHITE):
    """Draw text on the screen"""
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

def draw_lives(surf, x, y, lives, img):
    """Draw player lives on the screen"""
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img, img_rect)

def draw_shield_bar(surf, x, y, pct):
    """Draw shield bar when player has shield power-up"""
    if pct <= 0:
        return
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (pct / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, BLUE, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

def show_menu():
    """Display the main menu"""
    screen.fill(BLACK)
    
    # Draw stars
    for star in stars:
        pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[3])
    
    # Draw title
    draw_text(screen, "STARSHIP DEFENDER", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_text(screen, "Arrow keys to move, Space to fire", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_text(screen, "Press ENTER to start", 18, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3/4)
    draw_text(screen, "Press Q to quit", 18, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3/4 + 30)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                    return True
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def show_game_over():
    """Display game over screen"""
    screen.fill(BLACK)
    
    # Draw stars
    for star in stars:
        pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[3])
    
    draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_text(screen, f"Final Score: {player.score}", 36, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_text(screen, "Press ENTER to play again", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3/4)
    draw_text(screen, "Press Q to quit", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3/4 + 30)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                    return True
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def reset_game():
    """Reset the game state for a new game"""
    global all_sprites, enemies, bullets, enemy_bullets, powerups, player
    global difficulty_timer, difficulty_level, spawn_rate
    
    # Clear all sprite groups
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    
    # Create new player
    player = Player()
    all_sprites.add(player)
    
    # Reset difficulty
    difficulty_timer = pygame.time.get_ticks()
    difficulty_level = 1
    spawn_rate = 0.02

# Main game loop
running = True
while running:
    # Keep the loop running at the right speed
    clock.tick(FPS)
    
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_state == GameState.PLAYING:
                player.shoot()
    
    # Update game state
    if game_state == GameState.MENU:
        if show_menu():
            game_state = GameState.PLAYING
            reset_game()
    
    elif game_state == GameState.GAME_OVER:
        if show_game_over():
            game_state = GameState.PLAYING
            reset_game()
    
    elif game_state == GameState.PLAYING:
        # Update all sprites
        all_sprites.update()
        
        # Move stars in background
        for i in range(len(stars)):
            stars[i][1] += stars[i][2]  # Move star down
            if stars[i][1] > SCREEN_HEIGHT:
                stars[i][0] = random.randint(0, SCREEN_WIDTH)
                stars[i][1] = 0
        
        # Spawn enemies
        if random.random() < spawn_rate:
            enemy_type = 1 if random.random() < 0.7 else 2  # 70% chance for type 1, 30% for type 2
            e = Enemy(enemy_type)
            all_sprites.add(e)
            enemies.add(e)
        
        # Check for collisions - player bullets hitting enemies
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, bullet_list in hits.items():
            enemy.health -= 1
            if enemy.health <= 0:
                player.score += enemy.score_value
                
                # Create explosion
                expl = Explosion(enemy.rect.center, 3)
                all_sprites.add(expl)
                if explosion_sound:
                    explosion_sound.play()
                
                # Chance to spawn power-up
                if random.random() < 0.2:  # 20% chance
                    pow = PowerUp(enemy.rect.center)
                    all_sprites.add(pow)
                    powerups.add(pow)
                
                enemy.kill()
        
        # Check for collisions - enemy bullets hitting player
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        for hit in hits:
            if player.shield > 0:
                # Shield absorbs the hit
                if explosion_sound:
                    explosion_sound.play()
            else:
                player.lives -= 1
                if explosion_sound:
                    explosion_sound.play()
                
                # Create explosion
                expl = Explosion(hit.rect.center, 2)
                all_sprites.add(expl)
                
                if player.lives > 0:
                    player.hide()
                else:
                    if game_over_sound:
                        game_over_sound.play()
                    game_state = GameState.GAME_OVER
        
        # Check for collisions - player ship hitting enemies
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for hit in hits:
            if player.shield > 0:
                # Shield absorbs the hit
                if explosion_sound:
                    explosion_sound.play()
                
                # Create explosion for the enemy
                expl = Explosion(hit.rect.center, 3)
                all_sprites.add(expl)
            else:
                player.lives -= 1
                if explosion_sound:
                    explosion_sound.play()
                
                # Create explosion
                expl = Explosion(hit.rect.center, 3)
                all_sprites.add(expl)
                
                if player.lives > 0:
                    player.hide()
                else:
                    if game_over_sound:
                        game_over_sound.play()
                    game_state = GameState.GAME_OVER
        
        # Check for collisions - player collecting power-ups
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for hit in hits:
            if powerup_sound:
                powerup_sound.play()
            player.apply_powerup(hit.type)
        
        # Increase difficulty over time
        now = pygame.time.get_ticks()
        if now - difficulty_timer > 30000:  # Every 30 seconds
            difficulty_timer = now
            difficulty_level += 1
            spawn_rate = min(0.1, spawn_rate * 1.2)  # Increase spawn rate, max 10%
            
            # Make existing enemies faster
            for enemy in enemies:
                enemy.speed_y += 0.5
                enemy.shoot_chance *= 1.2  # Increase shooting frequency
        
        # Draw / render
        screen.fill(BLACK)
        
        # Draw stars
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[3])
        
        # Draw all sprites
        all_sprites.draw(screen)
        
        # Draw UI
        draw_text(screen, str(player.score), 18, SCREEN_WIDTH // 2, 10)
        draw_lives(screen, SCREEN_WIDTH - 100, 5, player.lives, pygame.transform.scale(player_img, (25, 25)))
        
        # Draw shield bar if player has shield
        if player.shield > 0:
            shield_pct = (player.power_up_end_time[PowerUpType.SHIELD] - pygame.time.get_ticks()) / 5000 * 100
            draw_shield_bar(screen, 5, 5, shield_pct)
        
        # Draw power-up indicators
        if player.double_shot:
            draw_text(screen, "DOUBLE SHOT", 14, 80, 30, GREEN)
        if player.rapid_fire:
            draw_text(screen, "RAPID FIRE", 14, 80, 50, YELLOW)
        
        # Draw difficulty level
        draw_text(screen, f"Level: {difficulty_level}", 18, 50, 10)
    
    # Flip the display
    pygame.display.flip()

pygame.quit()
