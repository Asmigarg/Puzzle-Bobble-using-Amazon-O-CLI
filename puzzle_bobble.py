import pygame
import sys
import math
import random
import os
import json
import time
from datetime import datetime

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BUBBLE_RADIUS = 20
GRID_SIZE = BUBBLE_RADIUS * 2
GRID_ROWS = 12
GRID_COLS = 16
SHOOTER_Y = HEIGHT - 50
SHOOT_SPEED = 20
MAX_ANGLE = 80  # Maximum shooting angle in degrees

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
PURPLE = (255, 50, 255)
CYAN = (50, 255, 255)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
PINK = (255, 105, 180)
LIME = (50, 205, 50)
TEAL = (0, 128, 128)

# List of bubble colors with gradients (center, outer)
BUBBLE_COLORS = [
    {"main": RED, "light": (255, 150, 150), "dark": (180, 0, 0)},
    {"main": GREEN, "light": (150, 255, 150), "dark": (0, 180, 0)},
    {"main": BLUE, "light": (150, 150, 255), "dark": (0, 0, 180)},
    {"main": YELLOW, "light": (255, 255, 150), "dark": (180, 180, 0)},
    {"main": PURPLE, "light": (255, 150, 255), "dark": (180, 0, 180)},
    {"main": CYAN, "light": (150, 255, 255), "dark": (0, 180, 180)},
    {"main": ORANGE, "light": (255, 200, 150), "dark": (180, 100, 0)}
]

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Puzzle Bobble")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 24)

# Load background image or create a gradient background
def create_background():
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        # Create a gradient from dark blue to lighter blue
        color = (20, 20, 50 + int(y / HEIGHT * 50))
        pygame.draw.line(background, color, (0, y), (WIDTH, y))
    
    # Add some decorative elements
    for _ in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        brightness = random.randint(150, 255)
        pygame.draw.circle(background, (brightness, brightness, brightness), (x, y), size)
    
    return background

background = create_background()

# Create bubble shine effect
def create_bubble_shine(radius):
    shine = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(shine, (255, 255, 255, 100), (radius, radius), radius)
    pygame.draw.circle(shine, (255, 255, 255, 150), (radius*0.7, radius*0.7), radius*0.2)
    return shine

bubble_shine = create_bubble_shine(BUBBLE_RADIUS)

# Create explosion animation frames
def create_explosion_frames(radius):
    frames = []
    for size in range(radius, 0, -5):
        frame = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(frame, (255, 255, 255, 150), (radius, radius), size)
        frames.append(frame)
    return frames

explosion_frames = create_explosion_frames(BUBBLE_RADIUS)

# Sound effects
try:
    pygame.mixer.init()
    shoot_sound = pygame.mixer.Sound(os.path.join("sounds", "shoot.wav"))
    pop_sound = pygame.mixer.Sound(os.path.join("sounds", "pop.wav"))
    fall_sound = pygame.mixer.Sound(os.path.join("sounds", "fall.wav"))
    game_over_sound = pygame.mixer.Sound(os.path.join("sounds", "game_over.wav"))
    sounds_loaded = True
except:
    sounds_loaded = False
    print("Sounds could not be loaded. Continuing without sound.")

class Particle:
    def __init__(self, x, y, color, size=3):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.lifetime = random.randint(20, 40)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
        return self.lifetime <= 0
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class Powerup:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.radius = BUBBLE_RADIUS * 0.8
        self.vy = 2  # Fall speed
        self.rotation = 0
        self.rotation_speed = random.uniform(2, 5)
        self.active = True
        self.shine_angle = random.uniform(0, 2*math.pi)
        self.shine_speed = random.uniform(0.05, 0.1)
        self.particles = []
        self.pulse_size = 0
        self.growing = True
        self.attraction_range = 100  # Range for auto-attraction
        self.attracted = False  # Flag for when powerup is being attracted
        self.attraction_speed = 0  # Initial attraction speed
        self.target_x = 0  # Target x position for attraction
        self.target_y = 0  # Target y position for attraction
        
        # Powerup types: "bomb", "rainbow", "lightning", "freeze", "magnet", "time_slow", "multi_shot"
        self.colors = {
            "bomb": (255, 50, 50),       # Red
            "rainbow": (255, 215, 0),    # Gold
            "lightning": (100, 100, 255), # Blue
            "freeze": (200, 200, 255),   # Light blue
            "magnet": (255, 105, 180),   # Pink
            "time_slow": (50, 205, 50),  # Lime
            "multi_shot": (0, 128, 128)  # Teal
        }
        
        # Create trail particles
        for _ in range(3):
            self.particles.append(Particle(self.x, self.y, self.colors[self.type], random.uniform(1, 3)))
    
    def update(self, shooter_x=None, shooter_y=None):
        # Check if powerup should be attracted to shooter
        if shooter_x is not None and shooter_y is not None:
            dx = shooter_x - self.x
            dy = shooter_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Start attraction if within range
            if distance < self.attraction_range and not self.attracted:
                self.attracted = True
                self.target_x = shooter_x
                self.target_y = shooter_y
            
            # Update position if being attracted
            if self.attracted:
                # Calculate direction to shooter
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Increase attraction speed over time
                self.attraction_speed += 0.2
                max_speed = 8.0
                self.attraction_speed = min(self.attraction_speed, max_speed)
                
                # Move toward shooter
                if distance > 0:
                    self.x += (dx / distance) * self.attraction_speed
                    self.y += (dy / distance) * self.attraction_speed
                
                # Create attraction particles
                if random.random() < 0.3:
                    self.particles.append(Particle(
                        self.x + random.uniform(-10, 10),
                        self.y + random.uniform(-10, 10),
                        self.colors[self.type],
                        random.uniform(1, 3)
                    ))
                
                return False  # Don't remove yet
        
        # Normal falling behavior if not attracted
        if not self.attracted:
            self.y += self.vy
        
        # Update rotation
        self.rotation += self.rotation_speed
        
        # Update shine effect
        self.shine_angle += self.shine_speed
        
        # Update pulse effect
        if self.growing:
            self.pulse_size += 0.2
            if self.pulse_size >= 5:
                self.growing = False
        else:
            self.pulse_size -= 0.2
            if self.pulse_size <= 0:
                self.growing = True
        
        # Update particles
        for particle in self.particles[:]:
            if particle.update():
                self.particles.remove(particle)
                
        # Add new trail particles
        if random.random() < 0.3:
            self.particles.append(Particle(self.x, self.y, self.colors[self.type], random.uniform(1, 3)))
        
        # Check if off screen
        if self.y > HEIGHT + self.radius:
            return True
        return False
    
    def draw(self):
        # Draw powerup
        color = self.colors[self.type]
        
        # Draw pulse effect
        if self.pulse_size > 0:
            pulse_surf = pygame.Surface((self.radius*2 + self.pulse_size*2, self.radius*2 + self.pulse_size*2), pygame.SRCALPHA)
            pulse_color = list(color) + [100 - self.pulse_size * 15]  # Add alpha value
            pygame.draw.circle(pulse_surf, pulse_color, 
                             (self.radius + self.pulse_size, self.radius + self.pulse_size), 
                             self.radius + self.pulse_size)
            pulse_rect = pulse_surf.get_rect(center=(self.x, self.y))
            screen.blit(pulse_surf, pulse_rect.topleft)
        
        # Draw with rotation effect
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        
        if self.type == "bomb":
            # Draw bomb
            pygame.draw.circle(surf, (50, 50, 50), (self.radius, self.radius), self.radius)
            pygame.draw.circle(surf, color, (self.radius, self.radius), self.radius * 0.8)
            # Draw fuse
            pygame.draw.line(surf, (100, 70, 30), 
                           (self.radius, self.radius - self.radius * 0.7), 
                           (self.radius + self.radius * 0.5, self.radius - self.radius * 1.2), 
                           3)
            # Draw spark
            spark_size = 2 + math.sin(pygame.time.get_ticks() * 0.01) * 2
            pygame.draw.circle(surf, (255, 255, 150), 
                             (self.radius + self.radius * 0.5, self.radius - self.radius * 1.2), 
                             spark_size)
            
            # Draw explosion lines
            for i in range(4):
                angle = i * math.pi / 2 + self.rotation * 0.01
                pygame.draw.line(surf, (255, 200, 50),
                               (self.radius, self.radius),
                               (self.radius + math.cos(angle) * self.radius * 0.7,
                                self.radius + math.sin(angle) * self.radius * 0.7),
                               2)
            
        elif self.type == "rainbow":
            # Draw rainbow powerup
            for i in range(6):
                angle = i * math.pi / 3
                r = self.radius * 0.8
                x = self.radius + r * math.cos(angle + self.rotation * 0.01)
                y = self.radius + r * math.sin(angle + self.rotation * 0.01)
                
                # Rainbow colors
                rainbow_colors = [(255,0,0), (255,165,0), (255,255,0), (0,255,0), (0,0,255), (128,0,128)]
                pygame.draw.circle(surf, rainbow_colors[i], (x, y), self.radius * 0.3)
            
            # Center circle
            pygame.draw.circle(surf, (255, 255, 255), (self.radius, self.radius), self.radius * 0.4)
            
            # Add sparkles
            for _ in range(2):
                sparkle_angle = random.uniform(0, 2*math.pi)
                sparkle_dist = random.uniform(0, self.radius * 0.7)
                sparkle_x = self.radius + math.cos(sparkle_angle) * sparkle_dist
                sparkle_y = self.radius + math.sin(sparkle_angle) * sparkle_dist
                sparkle_size = random.uniform(1, 2)
                pygame.draw.circle(surf, (255, 255, 255), (sparkle_x, sparkle_y), sparkle_size)
            
        elif self.type == "lightning":
            # Draw lightning powerup
            pygame.draw.circle(surf, (100, 100, 200), (self.radius, self.radius), self.radius)
            
            # Draw lightning bolt
            bolt_offset = math.sin(pygame.time.get_ticks() * 0.01) * self.radius * 0.2
            points = [
                (self.radius - self.radius * 0.2 + bolt_offset, self.radius - self.radius * 0.8),
                (self.radius + bolt_offset, self.radius - self.radius * 0.2),
                (self.radius - self.radius * 0.3 + bolt_offset, self.radius),
                (self.radius + self.radius * 0.2 + bolt_offset, self.radius + self.radius * 0.8)
            ]
            pygame.draw.polygon(surf, (255, 255, 100), points)
            
            # Add electric sparks
            for _ in range(3):
                spark_angle = random.uniform(0, 2*math.pi)
                spark_dist = self.radius * 0.8
                spark_x = self.radius + math.cos(spark_angle) * spark_dist
                spark_y = self.radius + math.sin(spark_angle) * spark_dist
                pygame.draw.line(surf, (200, 200, 255),
                               (self.radius, self.radius),
                               (spark_x, spark_y),
                               1)
            
        elif self.type == "freeze":
            # Draw freeze powerup
            pygame.draw.circle(surf, (200, 200, 255), (self.radius, self.radius), self.radius)
            
            # Draw snowflake
            for i in range(6):
                angle = i * math.pi / 3 + self.rotation * 0.01
                pygame.draw.line(surf, (255, 255, 255),
                               (self.radius, self.radius),
                               (self.radius + self.radius * 0.8 * math.cos(angle),
                                self.radius + self.radius * 0.8 * math.sin(angle)),
                               2)
                
                # Draw small lines on each arm
                mid_x = self.radius + self.radius * 0.4 * math.cos(angle)
                mid_y = self.radius + self.radius * 0.4 * math.sin(angle)
                perp_angle = angle + math.pi/2
                
                pygame.draw.line(surf, (255, 255, 255),
                               (mid_x, mid_y),
                               (mid_x + self.radius * 0.2 * math.cos(perp_angle),
                                mid_y + self.radius * 0.2 * math.sin(perp_angle)),
                               2)
                pygame.draw.line(surf, (255, 255, 255),
                               (mid_x, mid_y),
                               (mid_x - self.radius * 0.2 * math.cos(perp_angle),
                                mid_y - self.radius * 0.2 * math.sin(perp_angle)),
                               2)
                
            # Add frost particles
            for _ in range(2):
                frost_angle = random.uniform(0, 2*math.pi)
                frost_dist = random.uniform(self.radius * 0.3, self.radius * 0.9)
                frost_x = self.radius + math.cos(frost_angle) * frost_dist
                frost_y = self.radius + math.sin(frost_angle) * frost_dist
                pygame.draw.circle(surf, (255, 255, 255, 150), (frost_x, frost_y), 1)
                
        elif self.type == "magnet":
            # Draw magnet powerup
            pygame.draw.circle(surf, (200, 100, 150), (self.radius, self.radius), self.radius)
            
            # Draw magnet shape
            magnet_width = self.radius * 1.2
            magnet_height = self.radius * 0.8
            
            # Draw horseshoe magnet
            pygame.draw.arc(surf, (150, 50, 100),
                          (self.radius - magnet_width/2, self.radius - magnet_height/2,
                           magnet_width, magnet_height),
                          0, math.pi, 3)
            
            # Draw magnet poles
            pole_height = self.radius * 0.4
            pygame.draw.rect(surf, (200, 50, 100),
                           (self.radius - magnet_width/2, self.radius - pole_height/2,
                            self.radius * 0.3, pole_height))
            pygame.draw.rect(surf, (200, 50, 100),
                           (self.radius + magnet_width/2 - self.radius * 0.3, self.radius - pole_height/2,
                            self.radius * 0.3, pole_height))
            
            # Draw magnetic field lines
            for i in range(3):
                angle = self.rotation * 0.01 + i * math.pi/3
                pygame.draw.arc(surf, (255, 200, 220),
                              (self.radius - magnet_width/2 - i*4, self.radius - magnet_height/2 - i*4,
                               magnet_width + i*8, magnet_height + i*8),
                              angle, angle + math.pi, 1)
                
        elif self.type == "time_slow":
            # Draw time slow powerup
            pygame.draw.circle(surf, (50, 150, 50), (self.radius, self.radius), self.radius)
            
            # Draw clock face
            pygame.draw.circle(surf, (200, 255, 200), (self.radius, self.radius), self.radius * 0.7)
            pygame.draw.circle(surf, (50, 150, 50), (self.radius, self.radius), self.radius * 0.1)
            
            # Draw clock hands
            # Hour hand
            hour_angle = self.rotation * 0.01
            hour_x = self.radius + math.cos(hour_angle) * self.radius * 0.4
            hour_y = self.radius + math.sin(hour_angle) * self.radius * 0.4
            pygame.draw.line(surf, (50, 100, 50), (self.radius, self.radius), (hour_x, hour_y), 3)
            
            # Minute hand
            minute_angle = self.rotation * 0.05
            minute_x = self.radius + math.cos(minute_angle) * self.radius * 0.6
            minute_y = self.radius + math.sin(minute_angle) * self.radius * 0.6
            pygame.draw.line(surf, (50, 100, 50), (self.radius, self.radius), (minute_x, minute_y), 2)
            
            # Draw clock ticks
            for i in range(12):
                tick_angle = i * math.pi / 6
                inner_x = self.radius + math.cos(tick_angle) * self.radius * 0.6
                inner_y = self.radius + math.sin(tick_angle) * self.radius * 0.6
                outer_x = self.radius + math.cos(tick_angle) * self.radius * 0.7
                outer_y = self.radius + math.sin(tick_angle) * self.radius * 0.7
                pygame.draw.line(surf, (50, 100, 50), (inner_x, inner_y), (outer_x, outer_y), 2)
                
        elif self.type == "multi_shot":
            # Draw multi-shot powerup
            pygame.draw.circle(surf, (0, 100, 100), (self.radius, self.radius), self.radius)
            
            # Draw multiple bubbles icon
            for i in range(3):
                offset_x = (i - 1) * self.radius * 0.6
                mini_bubble_x = self.radius + offset_x
                mini_bubble_y = self.radius
                
                # Draw mini bubble
                pygame.draw.circle(surf, (100, 200, 200), (mini_bubble_x, mini_bubble_y), self.radius * 0.3)
                pygame.draw.circle(surf, (150, 255, 255), (mini_bubble_x, mini_bubble_y), self.radius * 0.2)
            
            # Draw arrows
            arrow_y_offset = self.radius * 0.5
            arrow_size = self.radius * 0.2
            
            # Left arrow
            pygame.draw.polygon(surf, (255, 255, 255), [
                (self.radius - self.radius * 0.6, self.radius - arrow_y_offset),
                (self.radius - self.radius * 0.6 - arrow_size, self.radius),
                (self.radius - self.radius * 0.6, self.radius + arrow_y_offset)
            ])
            
            # Right arrow
            pygame.draw.polygon(surf, (255, 255, 255), [
                (self.radius + self.radius * 0.6, self.radius - arrow_y_offset),
                (self.radius + self.radius * 0.6 + arrow_size, self.radius),
                (self.radius + self.radius * 0.6, self.radius + arrow_y_offset)
            ])
        
        # Draw shine effect
        shine_x = self.radius + math.cos(self.shine_angle) * self.radius * 0.5
        shine_y = self.radius + math.sin(self.shine_angle) * self.radius * 0.5
        pygame.draw.circle(surf, (255, 255, 255, 150), (int(shine_x), int(shine_y)), self.radius // 4)
        
        # Rotate and draw
        rotated_surf = pygame.transform.rotate(surf, self.rotation)
        rotated_rect = rotated_surf.get_rect(center=(self.x, self.y))
        screen.blit(rotated_surf, rotated_rect.topleft)
        
        # Draw particles
        for particle in self.particles:
            particle.draw()
    
    def check_collision(self, x, y, radius):
        # Check if powerup collides with given coordinates
        dx = self.x - x
        dy = self.y - y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.radius + radius

class Explosion:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.frame = 0
        self.max_frames = len(explosion_frames)
        self.particles = []
        for _ in range(20):
            self.particles.append(Particle(x, y, color))
    
    def update(self):
        self.frame += 1
        for particle in self.particles[:]:
            if particle.update():
                self.particles.remove(particle)
        return self.frame >= self.max_frames and not self.particles
    
    def draw(self):
        if self.frame < self.max_frames:
            screen.blit(explosion_frames[self.frame], 
                       (self.x - BUBBLE_RADIUS, self.y - BUBBLE_RADIUS))
        for particle in self.particles:
            particle.draw()

class Bubble:
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color if color else random.choice(BUBBLE_COLORS)
        self.radius = BUBBLE_RADIUS
        self.vx = 0  # Horizontal velocity
        self.vy = 0  # Vertical velocity
        self.row = 0
        self.col = 0
        self.marked = False  # For marking during matching
        self.falling = False
        self.fall_speed = 0
        self.shine_angle = random.uniform(0, 2*math.pi)  # For shine effect animation
        self.shine_speed = random.uniform(0.02, 0.05)
        self.is_rainbow = False  # For rainbow powerup
    
    def draw(self):
        # Draw bubble with gradient
        pygame.draw.circle(screen, self.color["dark"], (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, self.color["main"], (int(self.x), int(self.y)), self.radius - 3)
        pygame.draw.circle(screen, self.color["light"], (int(self.x), int(self.y)), self.radius - 6)
        
        # Draw rainbow effect if applicable
        if hasattr(self, 'is_rainbow') and self.is_rainbow:
            # Draw rainbow ring
            for i in range(6):
                angle = i * math.pi / 3 + pygame.time.get_ticks() * 0.002
                r = self.radius * 0.7
                x = self.x + r * math.cos(angle)
                y = self.y + r * math.sin(angle)
                
                # Rainbow colors
                rainbow_colors = [(255,0,0), (255,165,0), (255,255,0), (0,255,0), (0,0,255), (128,0,128)]
                pygame.draw.circle(screen, rainbow_colors[i], (int(x), int(y)), self.radius * 0.2)
        
        # Draw shine effect
        shine_x = self.x + math.cos(self.shine_angle) * self.radius * 0.5
        shine_y = self.y + math.sin(self.shine_angle) * self.radius * 0.5
        pygame.draw.circle(screen, (255, 255, 255, 150), (int(shine_x), int(shine_y)), self.radius // 4)
        
        # Update shine position for animation
        self.shine_angle += self.shine_speed
    
    def update(self):
        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy
        
        # Bounce off walls
        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx = -self.vx
            # Adjust position to prevent sticking to wall
            if self.x - self.radius <= 0:
                self.x = self.radius
            else:
                self.x = WIDTH - self.radius
    
    def update_fall(self):
        if self.falling:
            self.fall_speed += 0.2  # Gravity
            self.y += self.fall_speed
            
            # Remove if off screen
            if self.y > HEIGHT + self.radius:
                return True
        return False

class Game:
    def __init__(self):
        self.reset_game()
    
    def reset_game(self):
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.bubbles = []  # All bubbles on the grid
        self.falling_bubbles = []  # Bubbles that are falling
        self.explosions = []  # Explosion animations
        self.particles = []  # Particle effects
        self.powerups = []  # Active powerups
        self.shooter_angle = 0  # Angle in degrees
        self.shooting_bubble = None
        self.next_bubble = self.create_random_bubble()
        self.score = 0
        self.level = 1
        self.game_over = False
        self.combo = 0  # Combo counter for consecutive matches
        self.active_powerup = None  # Currently active powerup effect
        self.powerup_timer = 0  # Timer for powerup effects
        self.multi_shot_count = 0  # Counter for multi-shot powerup
        self.magnet_bubbles = []  # Bubbles affected by magnet
        self.time_slow_factor = 1.0  # Time slow factor (1.0 = normal speed)
        self.powerup_collection_count = 0  # Count of collected powerups
        self.powerup_stats = {  # Stats for each powerup type
            "bomb": 0,
            "rainbow": 0,
            "lightning": 0,
            "freeze": 0,
            "magnet": 0,
            "time_slow": 0,
            "multi_shot": 0
        }
        self.stored_powerup = None  # Powerup stored for later use
        self.game_time = 0  # Game time in seconds
        self.shots_fired = 0  # Number of shots fired
        
        # Initialize the grid with bubbles
        self.initialize_grid()
    
    def initialize_grid(self):
        # Fill the top rows with bubbles
        rows_to_fill = min(5, GRID_ROWS)
        for row in range(rows_to_fill):
            for col in range(GRID_COLS):
                # Skip some bubbles randomly for a more interesting pattern
                if random.random() < 0.3:
                    continue
                    
                # Offset even rows
                x_offset = BUBBLE_RADIUS if row % 2 == 0 else 0
                x = col * GRID_SIZE + BUBBLE_RADIUS + x_offset
                y = row * GRID_SIZE + BUBBLE_RADIUS
                
                color = random.choice(BUBBLE_COLORS)
                bubble = Bubble(x, y, color)
                bubble.row = row
                bubble.col = col
                self.bubbles.append(bubble)
                self.grid[row][col] = bubble
    
    def create_random_bubble(self):
        return Bubble(WIDTH // 2, SHOOTER_Y)
    
    def shoot_bubble(self, auto=False):
        if self.shooting_bubble is None and not self.game_over:
            # Create a new bubble at the shooter position
            self.shooting_bubble = Bubble(WIDTH // 2, SHOOTER_Y, self.next_bubble.color)
            
            # Calculate velocity based on angle
            angle_rad = math.radians(self.shooter_angle)
            self.shooting_bubble.vx = SHOOT_SPEED * math.sin(angle_rad)
            self.shooting_bubble.vy = -SHOOT_SPEED * math.cos(angle_rad)
            
            # Create new next bubble
            self.next_bubble = self.create_random_bubble()
            
            # Increment shots fired counter
            if not auto:
                self.shots_fired += 1
            
            # Play sound
            if sounds_loaded and not auto:
                shoot_sound.play()
    
    def update(self):
        # Apply time slow effect if active
        time_factor = self.time_slow_factor if self.active_powerup == "time_slow" else 1.0
        
        # Update shooting bubble
        if self.shooting_bubble:
            # Apply time slow to shooting bubble
            original_vx = self.shooting_bubble.vx
            original_vy = self.shooting_bubble.vy
            self.shooting_bubble.vx *= time_factor
            self.shooting_bubble.vy *= time_factor
            
            self.shooting_bubble.update()
            
            # Restore original velocity
            self.shooting_bubble.vx = original_vx
            self.shooting_bubble.vy = original_vy
            
            # Check if bubble hits top
            if self.shooting_bubble.y - BUBBLE_RADIUS <= 0:
                self.attach_bubble(self.shooting_bubble)
                # Handle multi-shot
                if self.active_powerup == "multi_shot" and self.multi_shot_count > 0:
                    self.multi_shot_count -= 1
                    self.shoot_bubble(auto=True)
                return
            
            # Check for collision with other bubbles
            for bubble in self.bubbles:
                dx = self.shooting_bubble.x - bubble.x
                dy = self.shooting_bubble.y - bubble.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < self.shooting_bubble.radius + bubble.radius:
                    self.attach_bubble(self.shooting_bubble)
                    # Handle multi-shot
                    if self.active_powerup == "multi_shot" and self.multi_shot_count > 0:
                        self.multi_shot_count -= 1
                        self.shoot_bubble(auto=True)
                    return
            
            # Apply magnet effect
            if self.active_powerup == "magnet":
                # Find closest bubble of same color
                closest_bubble = None
                closest_dist = float('inf')
                
                for bubble in self.bubbles:
                    if bubble.color == self.shooting_bubble.color:
                        dx = bubble.x - self.shooting_bubble.x
                        dy = bubble.y - self.shooting_bubble.y
                        dist = math.sqrt(dx*dx + dy*dy)
                        
                        if dist < closest_dist and dist < 200:  # Only attract within range
                            closest_bubble = bubble
                            closest_dist = dist
                
                # Apply attraction force
                if closest_bubble:
                    attraction_strength = 0.5  # Adjust as needed
                    dx = closest_bubble.x - self.shooting_bubble.x
                    dy = closest_bubble.y - self.shooting_bubble.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    # Normalize and apply force
                    if dist > 0:
                        self.shooting_bubble.vx += (dx / dist) * attraction_strength
                        self.shooting_bubble.vy += (dy / dist) * attraction_strength
                        
                        # Limit maximum velocity
                        speed = math.sqrt(self.shooting_bubble.vx**2 + self.shooting_bubble.vy**2)
                        if speed > SHOOT_SPEED * 1.5:
                            self.shooting_bubble.vx = (self.shooting_bubble.vx / speed) * SHOOT_SPEED * 1.5
                            self.shooting_bubble.vy = (self.shooting_bubble.vy / speed) * SHOOT_SPEED * 1.5
                    
                    # Add magnetic particles
                    if random.random() < 0.2:
                        mid_x = (self.shooting_bubble.x + closest_bubble.x) / 2
                        mid_y = (self.shooting_bubble.y + closest_bubble.y) / 2
                        self.particles.append(MagneticParticle(
                            self.shooting_bubble.x, self.shooting_bubble.y,
                            mid_x + random.uniform(-20, 20), mid_y + random.uniform(-20, 20),
                            (255, 100, 200)
                        ))
        
        # Update falling bubbles
        for bubble in self.falling_bubbles[:]:
            if bubble.update_fall():
                self.falling_bubbles.remove(bubble)
        
        # Update explosions
        for explosion in self.explosions[:]:
            if explosion.update():
                self.explosions.remove(explosion)
        
        # Update particles
        for particle in self.particles[:]:
            if particle.update():
                self.particles.remove(particle)
        
        # Update powerups - pass shooter position for auto-attraction
        shooter_x = self.shooting_bubble.x if self.shooting_bubble else WIDTH // 2
        shooter_y = self.shooting_bubble.y if self.shooting_bubble else SHOOTER_Y
        
        for powerup in self.powerups[:]:
            if powerup.update(shooter_x, shooter_y):
                self.powerups.remove(powerup)
            elif self.shooting_bubble and powerup.check_collision(self.shooting_bubble.x, self.shooting_bubble.y, self.shooting_bubble.radius):
                self.activate_powerup(powerup)
                self.powerups.remove(powerup)
        
        # Update powerup timer
        if self.active_powerup:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                # Special cleanup for some powerups
                if self.active_powerup == "multi_shot":
                    self.multi_shot_count = 0
                elif self.active_powerup == "time_slow":
                    self.time_slow_factor = 1.0
                
                self.active_powerup = None
    
    def activate_powerup(self, powerup):
        # If we already have a stored powerup and this isn't an instant effect,
        # store the new one and activate the old one
        if self.stored_powerup and powerup.type not in ["bomb", "lightning"]:
            old_powerup = self.stored_powerup
            self.stored_powerup = powerup
            
            # Create a notification
            self.particles.append(PowerupNotification(WIDTH - 100, 200, 
                                                    f"{powerup.type.upper()} stored!",
                                                    powerup.colors[powerup.type]))
            
            # Activate the old powerup
            powerup = old_powerup
        
        self.active_powerup = powerup.type
        self.powerup_timer = 300  # 5 seconds at 60 FPS
        
        # Create explosion effect
        self.explosions.append(Explosion(powerup.x, powerup.y, powerup.colors[powerup.type]))
        
        # Add score
        self.score += 50
        self.add_score_popup(powerup.x, powerup.y, 50)
        
        # Update powerup stats
        self.powerup_collection_count += 1
        self.powerup_stats[powerup.type] += 1
        
        # Debug print
        print(f"Activated {powerup.type} powerup")
        
        # Play sound
        if sounds_loaded:
            pop_sound.play()
        
        # Apply powerup effect
        if powerup.type == "bomb":
            # Bomb: Destroy bubbles in an area
            self.apply_bomb_powerup(powerup.x, powerup.y)
            # Reset active powerup since this is an instant effect
            self.active_powerup = None
            
        elif powerup.type == "rainbow":
            # Rainbow: Change shooting bubble to rainbow (matches any color)
            if self.shooting_bubble:
                # Create rainbow color effect
                rainbow_color = {
                    "main": GOLD,
                    "light": (255, 255, 150),
                    "dark": (200, 150, 0)
                }
                self.shooting_bubble.color = rainbow_color
                self.shooting_bubble.is_rainbow = True
                print("Applied rainbow effect to shooting bubble")
                
        elif powerup.type == "lightning":
            # Lightning: Clear a vertical column
            self.apply_lightning_powerup()
            # Reset active powerup since this is an instant effect
            self.active_powerup = None
            
        elif powerup.type == "freeze":
            # Freeze: Slow down the game temporarily (visual effect only)
            # This is handled by the powerup timer
            pass
            
        elif powerup.type == "magnet":
            # Magnet: Attract bubbles of the same color
            # This is handled in the update method
            pass
            
        elif powerup.type == "time_slow":
            # Time Slow: Slow down the shooting bubble
            self.time_slow_factor = 0.5  # Half speed
            
        elif powerup.type == "multi_shot":
            # Multi-Shot: Shoot multiple bubbles in sequence
            self.multi_shot_count = 3  # Number of extra shots
    
    def apply_bomb_powerup(self, x, y):
        # Find the closest grid position
        row, col = self.find_grid_position(x, y)
        
        # Define blast radius (in grid cells)
        blast_radius = 3  # Increased from 2
        
        # Find all bubbles in blast radius
        bubbles_to_remove = []
        for r in range(max(0, row - blast_radius), min(GRID_ROWS, row + blast_radius + 1)):
            for c in range(max(0, col - blast_radius), min(GRID_COLS, col + blast_radius + 1)):
                if self.grid[r][c]:
                    # Check if within circular blast radius
                    dr = r - row
                    dc = c - col
                    if dr*dr + dc*dc <= blast_radius*blast_radius:
                        bubbles_to_remove.append(self.grid[r][c])
        
        # Create explosion for each bubble
        for bubble in bubbles_to_remove:
            self.explosions.append(Explosion(bubble.x, bubble.y, bubble.color["main"]))
            
            # Add extra particles for bigger explosion
            for _ in range(10):
                angle = random.uniform(0, 2*math.pi)
                distance = random.uniform(0, bubble.radius * 2)
                particle_x = bubble.x + math.cos(angle) * distance
                particle_y = bubble.y + math.sin(angle) * distance
                self.particles.append(Particle(particle_x, particle_y, bubble.color["main"], random.uniform(2, 5)))
        
        # Create shockwave effect
        for i in range(5):
            self.particles.append(ShockwaveParticle(x, y, blast_radius * GRID_SIZE * (i+1) / 5))
        
        # Remove bubbles
        self.remove_bubbles(bubbles_to_remove)
        
        # Add score
        bomb_score = len(bubbles_to_remove) * 15
        self.score += bomb_score
        self.add_score_popup(x, y, bomb_score)
        
        # Check for floating bubbles
        self.check_floating_bubbles()
    
    def apply_lightning_powerup(self):
        # Find a column with the most bubbles
        column_counts = [0] * GRID_COLS
        for bubble in self.bubbles:
            column_counts[bubble.col] += 1
        
        # Find column with most bubbles
        target_col = column_counts.index(max(column_counts))
        
        # Remove all bubbles in that column
        bubbles_to_remove = []
        for r in range(GRID_ROWS):
            if self.grid[r][target_col]:
                bubbles_to_remove.append(self.grid[r][target_col])
        
        # Create lightning effect
        for y in range(0, HEIGHT, 10):  # More frequent lightning particles
            x = target_col * GRID_SIZE + BUBBLE_RADIUS
            if target_col % 2 == 1:
                x += BUBBLE_RADIUS  # Offset for odd rows
            
            # Create lightning particle with random offset
            offset = random.uniform(-10, 10)
            self.particles.append(LightningParticle(x + offset, y))
            
            # Add some branching lightning
            if random.random() < 0.2:
                branch_x = x + random.uniform(-30, 30)
                branch_y = y + random.uniform(-20, 20)
                self.particles.append(LightningParticle(branch_x, branch_y))
        
        # Create explosion for each bubble
        for bubble in bubbles_to_remove:
            self.explosions.append(Explosion(bubble.x, bubble.y, bubble.color["main"]))
            
            # Add electric particles
            for _ in range(5):
                self.particles.append(ElectricParticle(bubble.x, bubble.y))
        
        # Remove bubbles
        self.remove_bubbles(bubbles_to_remove)
        
        # Add score
        lightning_score = len(bubbles_to_remove) * 20
        self.score += lightning_score
        if bubbles_to_remove:
            self.add_score_popup(bubbles_to_remove[0].x, bubbles_to_remove[0].y, lightning_score)
        
        # Check for floating bubbles
        self.check_floating_bubbles()
    
    def attach_bubble(self, bubble):
        # Find the closest grid position
        row, col = self.find_grid_position(bubble.x, bubble.y)
        
        # Ensure valid grid position
        if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
            self.shooting_bubble = None
            return
        
        # If position is already occupied, find a nearby empty spot
        if self.grid[row][col]:
            neighbors = self.get_neighbors(row, col)
            for nrow, ncol in neighbors:
                if 0 <= nrow < GRID_ROWS and 0 <= ncol < GRID_COLS and not self.grid[nrow][ncol]:
                    row, col = nrow, ncol
                    break
            else:
                # No empty spot found
                self.shooting_bubble = None
                return
        
        # Adjust position to grid
        x_offset = BUBBLE_RADIUS if row % 2 == 0 else 0
        bubble.x = col * GRID_SIZE + BUBBLE_RADIUS + x_offset
        bubble.y = row * GRID_SIZE + BUBBLE_RADIUS
        bubble.row = row
        bubble.col = col
        
        # Add to grid and bubbles list
        self.grid[row][col] = bubble
        self.bubbles.append(bubble)
        
        # Check for matches
        matches = self.find_matches(bubble)
        
        # Debug print
        print(f"Found {len(matches)} matches")
        
        if len(matches) >= 3:
            # Increase combo
            self.combo += 1
            combo_multiplier = min(5, self.combo)
            
            # Add score with combo multiplier
            match_score = len(matches) * 10 * combo_multiplier
            self.score += match_score
            
            # Create score popup
            self.add_score_popup(bubble.x, bubble.y, match_score)
            
            # Create explosions for each matched bubble
            for match in matches:
                self.explosions.append(Explosion(match.x, match.y, match.color["main"]))
            
            # Remove matched bubbles
            self.remove_bubbles(matches)
            
            # Chance to spawn powerup (higher chance with bigger matches)
            if random.random() < 0.1 + min(0.4, len(matches) * 0.05):
                # Choose a random powerup type
                powerup_type = random.choice(["bomb", "rainbow", "lightning", "freeze"])
                
                # Create powerup at bubble position
                self.powerups.append(Powerup(bubble.x, bubble.y, powerup_type))
            
            # Play sound
            if sounds_loaded:
                pop_sound.play()
        else:
            # Reset combo if no match
            self.combo = 0
        
        # Check for floating bubbles
        floating = self.check_floating_bubbles()
        if floating:
            # Add score for floating bubbles
            float_score = len(floating) * 5
            self.score += float_score
            
            # Create score popup
            if floating:
                self.add_score_popup(floating[0].x, floating[0].y, float_score)
            
            # Play sound
            if sounds_loaded:
                fall_sound.play()
        
        # Check for game over (bubbles reaching bottom)
        for bubble in self.bubbles:
            if bubble.row >= GRID_ROWS - 1:
                self.game_over = True
                if sounds_loaded:
                    game_over_sound.play()
                break
        
        # Reset shooting bubble
        self.shooting_bubble = None
    
    def find_grid_position(self, x, y):
        # Convert pixel position to grid position
        row = int(y / GRID_SIZE)
        
        # Adjust for offset in even rows
        if row % 2 == 0:
            col = int((x - BUBBLE_RADIUS) / GRID_SIZE)
        else:
            col = int(x / GRID_SIZE)
        
        return row, col
    
    def get_neighbors(self, row, col):
        neighbors = []
        
        # Directions depend on whether row is even or odd
        if row % 2 == 0:  # Even row
            directions = [
                (-1, -1), (-1, 0),  # Above
                (0, -1), (0, 1),    # Left and right
                (1, -1), (1, 0)     # Below
            ]
        else:  # Odd row
            directions = [
                (-1, 0), (-1, 1),  # Above
                (0, -1), (0, 1),   # Left and right
                (1, 0), (1, 1)     # Below
            ]
        
        for dr, dc in directions:
            neighbors.append((row + dr, col + dc))
        
        return neighbors
    
    def find_matches(self, bubble):
        # Reset all marked flags
        for b in self.bubbles:
            b.marked = False
        
        matches = []
        
        # Handle rainbow bubble (matches any color)
        if hasattr(bubble, 'is_rainbow') and bubble.is_rainbow:
            # Find all adjacent bubbles
            neighbors = []
            for nrow, ncol in self.get_neighbors(bubble.row, bubble.col):
                if 0 <= nrow < GRID_ROWS and 0 <= ncol < GRID_COLS and self.grid[nrow][ncol]:
                    neighbors.append(self.grid[nrow][ncol])
            
            # If there are neighbors, pick the color with the most matches
            if neighbors:
                best_matches = []
                for neighbor in neighbors:
                    # Temporarily set the rainbow bubble to this color
                    original_color = bubble.color
                    bubble.color = neighbor.color
                    
                    # Find matches with this color
                    temp_matches = []
                    self.find_matching_neighbors(bubble, temp_matches)
                    
                    # Reset marked flags
                    for b in self.bubbles:
                        b.marked = False
                    
                    # Keep track of best matches
                    if len(temp_matches) > len(best_matches):
                        best_matches = temp_matches
                    
                    # Restore original color
                    bubble.color = original_color
                
                # Use the best matches
                matches = best_matches
                
                # Debug print
                print(f"Rainbow bubble found {len(matches)} best matches")
            else:
                # No neighbors, just return the bubble itself
                matches = [bubble]
        else:
            # Normal matching
            self.find_matching_neighbors(bubble, matches)
        
        return matches
    
    def find_matching_neighbors(self, bubble, matches):
        if bubble is None or bubble.marked:
            return
        
        bubble.marked = True
        matches.append(bubble)
        
        # Get neighbors
        neighbors = []
        for nrow, ncol in self.get_neighbors(bubble.row, bubble.col):
            if 0 <= nrow < GRID_ROWS and 0 <= ncol < GRID_COLS:
                neighbors.append(self.grid[nrow][ncol])
        
        # Check each neighbor
        for neighbor in neighbors:
            # Debug print to check color matching
            if neighbor and not neighbor.marked:
                # Compare colors properly - need to compare the actual color dictionaries
                same_color = False
                if hasattr(bubble, 'is_rainbow') and bubble.is_rainbow:
                    same_color = True
                elif hasattr(neighbor, 'is_rainbow') and neighbor.is_rainbow:
                    same_color = True
                else:
                    # Compare the main color values
                    same_color = (neighbor.color["main"] == bubble.color["main"])
                
                if same_color:
                    self.find_matching_neighbors(neighbor, matches)
    
    def remove_bubbles(self, bubbles):
        for bubble in bubbles:
            if bubble in self.bubbles:
                self.bubbles.remove(bubble)
                self.grid[bubble.row][bubble.col] = None
                
                # Create particles
                for _ in range(10):
                    self.particles.append(Particle(bubble.x, bubble.y, bubble.color["main"]))
    
    def check_floating_bubbles(self):
        # Mark all bubbles as not visited
        for bubble in self.bubbles:
            bubble.marked = False
        
        # Mark all bubbles connected to the top
        for col in range(GRID_COLS):
            if self.grid[0][col]:
                self.mark_connected(self.grid[0][col])
        
        # Find all unmarked bubbles (floating)
        floating = [b for b in self.bubbles if not b.marked]
        
        # Make them fall
        for bubble in floating:
            bubble.falling = True
            self.falling_bubbles.append(bubble)
            self.bubbles.remove(bubble)
            self.grid[bubble.row][bubble.col] = None
        
        return floating
    
    def mark_connected(self, bubble):
        if bubble is None or bubble.marked:
            return
        
        bubble.marked = True
        
        # Mark all connected neighbors
        neighbors = []
        for nrow, ncol in self.get_neighbors(bubble.row, bubble.col):
            if 0 <= nrow < GRID_ROWS and 0 <= ncol < GRID_COLS:
                neighbors.append(self.grid[nrow][ncol])
        
        for neighbor in neighbors:
            if neighbor:
                self.mark_connected(neighbor)
    
    def add_score_popup(self, x, y, score):
        # Create a score popup particle
        for digit in str(score):
            self.particles.append(ScoreParticle(x, y, digit))
            x += 10  # Offset each digit
    
    def draw(self):
        # Draw background
        screen.blit(background, (0, 0))
        
        # Apply freeze effect if active
        if self.active_powerup == "freeze":
            # Draw freeze overlay
            freeze_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            freeze_overlay.fill((200, 220, 255, 30))
            screen.blit(freeze_overlay, (0, 0))
            
            # Add snowflakes
            for _ in range(10):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                size = random.randint(1, 3)
                pygame.draw.circle(screen, (255, 255, 255, 150), (x, y), size)
        
        # Draw grid bubbles
        for bubble in self.bubbles:
            bubble.draw()
        
        # Draw falling bubbles
        for bubble in self.falling_bubbles:
            bubble.draw()
        
        # Draw shooting bubble
        if self.shooting_bubble:
            self.shooting_bubble.draw()
        
        # Draw explosions
        for explosion in self.explosions:
            explosion.draw()
        
        # Draw particles
        for particle in self.particles:
            particle.draw()
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw()
        
        # Draw next bubble
        next_bubble_text = font.render("Next:", True, WHITE)
        screen.blit(next_bubble_text, (WIDTH - 150, 50))
        
        # Draw next bubble with gradient
        next_x, next_y = WIDTH - 100, 100
        pygame.draw.circle(screen, self.next_bubble.color["dark"], (next_x, next_y), BUBBLE_RADIUS)
        pygame.draw.circle(screen, self.next_bubble.color["main"], (next_x, next_y), BUBBLE_RADIUS - 3)
        pygame.draw.circle(screen, self.next_bubble.color["light"], (next_x, next_y), BUBBLE_RADIUS - 6)
        
        # Draw stored powerup if available
        if self.stored_powerup:
            stored_text = font.render("Stored:", True, WHITE)
            screen.blit(stored_text, (WIDTH - 150, 150))
            
            # Draw mini powerup
            stored_x, stored_y = WIDTH - 100, 180
            
            # Create a temporary surface for the powerup
            powerup_surf = pygame.Surface((BUBBLE_RADIUS*2, BUBBLE_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(powerup_surf, self.stored_powerup.colors[self.stored_powerup.type], 
                             (BUBBLE_RADIUS, BUBBLE_RADIUS), BUBBLE_RADIUS)
            
            # Draw the powerup icon
            screen.blit(powerup_surf, (stored_x - BUBBLE_RADIUS, stored_y - BUBBLE_RADIUS))
            
            # Draw powerup name
            powerup_names = {
                "bomb": "BOMB",
                "rainbow": "RAINBOW",
                "lightning": "LIGHTNING",
                "freeze": "FREEZE",
                "magnet": "MAGNET",
                "time_slow": "TIME SLOW",
                "multi_shot": "MULTI-SHOT"
            }
            
            name_text = font.render(powerup_names[self.stored_powerup.type], True, 
                                  self.stored_powerup.colors[self.stored_powerup.type])
            screen.blit(name_text, (WIDTH - 150, 210))
            
            # Draw use instruction
            use_text = pygame.font.SysFont('Arial', 16).render("Press SPACE to use", True, WHITE)
            screen.blit(use_text, (WIDTH - 150, 235))
        
        # Draw shooter
        # Base
        pygame.draw.circle(screen, (100, 100, 100), (WIDTH // 2, SHOOTER_Y), 25)
        pygame.draw.circle(screen, (150, 150, 150), (WIDTH // 2, SHOOTER_Y), 20)
        
        # Barrel
        angle_rad = math.radians(self.shooter_angle)
        end_x = WIDTH // 2 + 60 * math.sin(angle_rad)
        end_y = SHOOTER_Y - 60 * math.cos(angle_rad)
        
        # Draw barrel with gradient
        pygame.draw.line(screen, (100, 100, 100), (WIDTH // 2, SHOOTER_Y), (end_x, end_y), 12)
        pygame.draw.line(screen, (150, 150, 150), (WIDTH // 2, SHOOTER_Y), (end_x, end_y), 8)
        
        # Draw aiming line
        for i in range(10):
            point_x = WIDTH // 2 + (i * 30 + 60) * math.sin(angle_rad)
            point_y = SHOOTER_Y - (i * 30 + 60) * math.cos(angle_rad)
            
            if 0 <= point_x < WIDTH and 0 <= point_y < HEIGHT:
                alpha = 255 - i * 25  # Fade out
                pygame.draw.circle(screen, (255, 255, 255, alpha), (int(point_x), int(point_y)), 2)
        
        # Draw score and level with shadow effect
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        combo_text = font.render(f"Combo: x{self.combo}" if self.combo > 0 else "", True, (255, 255, 0))
        time_text = font.render(f"Time: {self.game_time//60}:{self.game_time%60:02d}", True, WHITE)
        shots_text = font.render(f"Shots: {self.shots_fired}", True, WHITE)
        
        # Draw text shadow
        shadow_offset = 2
        score_shadow = font.render(f"Score: {self.score}", True, BLACK)
        level_shadow = font.render(f"Level: {self.level}", True, BLACK)
        
        screen.blit(score_shadow, (20 + shadow_offset, 20 + shadow_offset))
        screen.blit(level_shadow, (20 + shadow_offset, 50 + shadow_offset))
        
        screen.blit(score_text, (20, 20))
        screen.blit(level_text, (20, 50))
        screen.blit(combo_text, (20, 80))
        screen.blit(time_text, (20, 110))
        screen.blit(shots_text, (20, 140))
        
        # Draw active powerup indicator
        if self.active_powerup:
            powerup_colors = {
                "bomb": (255, 50, 50),
                "rainbow": (255, 215, 0),
                "lightning": (100, 100, 255),
                "freeze": (200, 200, 255),
                "magnet": (255, 105, 180),
                "time_slow": (50, 205, 50),
                "multi_shot": (0, 128, 128)
            }
            
            powerup_names = {
                "bomb": "BOMB",
                "rainbow": "RAINBOW",
                "lightning": "LIGHTNING",
                "freeze": "FREEZE",
                "magnet": "MAGNET",
                "time_slow": "TIME SLOW",
                "multi_shot": "MULTI-SHOT"
            }
            
            # Draw powerup name with timer
            powerup_text = font.render(f"Active: {powerup_names[self.active_powerup]}: {self.powerup_timer//60}s", 
                                     True, powerup_colors[self.active_powerup])
            screen.blit(powerup_text, (20, 170))
            
            # Draw additional info for multi-shot
            if self.active_powerup == "multi_shot" and self.multi_shot_count > 0:
                shots_text = font.render(f"Shots left: {self.multi_shot_count}", True, powerup_colors["multi_shot"])
                screen.blit(shots_text, (20, 200))
        
        # Draw powerup collection stats in corner
        if self.powerup_collection_count > 0:
            stats_x = WIDTH - 180
            stats_y = HEIGHT - 120
            stats_text = font.render("Powerups:", True, WHITE)
            screen.blit(stats_text, (stats_x, stats_y))
            
            # Draw mini icons for each collected powerup type
            y_offset = 30
            for powerup_type, count in self.powerup_stats.items():
                if count > 0:
                    # Draw mini powerup icon
                    powerup_colors = {
                        "bomb": (255, 50, 50),
                        "rainbow": (255, 215, 0),
                        "lightning": (100, 100, 255),
                        "freeze": (200, 200, 255),
                        "magnet": (255, 105, 180),
                        "time_slow": (50, 205, 50),
                        "multi_shot": (0, 128, 128)
                    }
                    
                    pygame.draw.circle(screen, powerup_colors[powerup_type], 
                                     (stats_x + 15, stats_y + y_offset), 10)
                    
                    # Draw count
                    count_text = font.render(f"x{count}", True, WHITE)
                    screen.blit(count_text, (stats_x + 30, stats_y + y_offset - 10))
                    
                    y_offset += 25
        
        # Draw game over
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Draw game over text with glow effect
            for offset in range(5, 0, -1):
                game_over_glow = font.render("Game Over", True, (255, 0, 0, 50))
                screen.blit(game_over_glow, 
                           (WIDTH // 2 - game_over_glow.get_width() // 2 + offset, 
                            HEIGHT // 2 - 100 + offset))
                screen.blit(game_over_glow, 
                           (WIDTH // 2 - game_over_glow.get_width() // 2 - offset, 
                            HEIGHT // 2 - 100 - offset))
            
            game_over_text = font.render("Game Over", True, (255, 0, 0))
            final_score_text = font.render(f"Final Score: {self.score}", True, WHITE)
            time_text = font.render(f"Time: {self.game_time//60}:{self.game_time%60:02d}", True, WHITE)
            shots_text = font.render(f"Shots: {self.shots_fired}", True, WHITE)
            efficiency_text = font.render(f"Efficiency: {int(self.score / max(1, self.shots_fired))} pts/shot", True, WHITE)
            
            restart_text = font.render("Press R to restart", True, WHITE)
            save_score_text = font.render("Press S to save score to leaderboard", True, (255, 255, 0))
            
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(shots_text, (WIDTH // 2 - shots_text.get_width() // 2, HEIGHT // 2))
            screen.blit(efficiency_text, (WIDTH // 2 - efficiency_text.get_width() // 2, HEIGHT // 2 + 30))
            
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 70))
            screen.blit(save_score_text, (WIDTH // 2 - save_score_text.get_width() // 2, HEIGHT // 2 + 100))

class ShockwaveParticle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = radius
        self.lifetime = 20
        self.width = 3
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self):
        alpha = min(255, self.lifetime * 12)
        progress = 1 - (self.lifetime / 20)
        current_radius = self.max_radius * progress
        pygame.draw.circle(screen, (255, 255, 255, alpha), (int(self.x), int(self.y)), int(current_radius), self.width)

class ElectricParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = random.randint(10, 20)
        self.points = []
        
        # Generate zigzag points
        num_points = random.randint(3, 6)
        angle = random.uniform(0, 2*math.pi)
        max_dist = random.uniform(10, 30)
        
        for i in range(num_points):
            dist = max_dist * (i / (num_points - 1))
            offset = random.uniform(-10, 10)
            point_x = self.x + math.cos(angle) * dist + offset
            point_y = self.y + math.sin(angle) * dist + offset
            self.points.append((point_x, point_y))
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self):
        alpha = min(255, self.lifetime * 12)
        if len(self.points) > 1:
            pygame.draw.lines(screen, (200, 200, 255, alpha), False, self.points, 2)

class MagneticParticle:
    def __init__(self, start_x, start_y, end_x, end_y, color):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.color = color
        self.lifetime = random.randint(10, 20)
        self.progress = 0
    
    def update(self):
        self.lifetime -= 1
        self.progress += 0.1
        if self.progress > 1:
            self.progress = 1
        return self.lifetime <= 0
    
    def draw(self):
        alpha = min(255, self.lifetime * 12)
        x = self.start_x + (self.end_x - self.start_x) * self.progress
        y = self.start_y + (self.end_y - self.start_y) * self.progress
        
        # Draw particle
        pygame.draw.circle(screen, self.color + (alpha,), (int(x), int(y)), 2)

class LightningParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = random.randint(10, 20)
        self.width = random.randint(2, 5)
        self.offset = random.uniform(-10, 10)
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self):
        # Draw lightning bolt
        alpha = min(255, self.lifetime * 15)
        pygame.draw.line(screen, (200, 200, 255, alpha), 
                       (self.x + self.offset, self.y), 
                       (self.x + self.offset, self.y + 20), 
                       self.width)

class PowerupNotification:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 60  # 1 second at 60 FPS
        self.font = pygame.font.SysFont('Arial', 18)
        self.alpha = 255
        self.scale = 0
        self.growing = True
    
    def update(self):
        if self.growing:
            self.scale += 0.1
            if self.scale >= 1.0:
                self.growing = False
        else:
            self.lifetime -= 1
            if self.lifetime < 30:
                self.alpha = int(255 * (self.lifetime / 30))
        
        return self.lifetime <= 0
    
    def draw(self):
        # Draw background
        text_surface = self.font.render(self.text, True, self.color)
        text_width, text_height = text_surface.get_size()
        
        # Apply scale
        scaled_width = int(text_width * self.scale)
        scaled_height = int(text_height * self.scale)
        
        if scaled_width > 0 and scaled_height > 0:
            scaled_surface = pygame.transform.scale(text_surface, (scaled_width, scaled_height))
            
            # Apply alpha
            scaled_surface.set_alpha(self.alpha)
            
            # Draw centered at position
            screen.blit(scaled_surface, 
                       (self.x - scaled_width // 2, 
                        self.y - scaled_height // 2))

class ScoreParticle:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.vy = -2  # Move upward
        self.lifetime = 30
        self.font = pygame.font.SysFont('Arial', 20)
    
    def update(self):
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime <= 0
    
    def draw(self):
        alpha = min(255, self.lifetime * 8)
        text_surface = self.font.render(self.text, True, (255, 255, 255, alpha))
        screen.blit(text_surface, (int(self.x), int(self.y)))

def show_instructions():
    # Create animated background bubbles
    background_bubbles = []
    for _ in range(30):  # Increased number of bubbles
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(10, 40)
        color_idx = random.randint(0, len(BUBBLE_COLORS) - 1)
        color = BUBBLE_COLORS[color_idx]["main"]
        alpha = random.randint(30, 100)  # Lighter bubbles with lower alpha
        vx = random.uniform(-0.5, 0.5)  # Horizontal velocity
        vy = random.uniform(-0.5, 0.5)  # Vertical velocity
        background_bubbles.append({
            "x": x, "y": y, "size": size, "color": color, 
            "alpha": alpha, "vx": vx, "vy": vy
        })
    
    waiting = True
    while waiting:
        # Clear screen with background
        screen.blit(background, (0, 0))
        
        # Update and draw animated background bubbles
        for bubble in background_bubbles:
            # Update position
            bubble["x"] += bubble["vx"]
            bubble["y"] += bubble["vy"]
            
            # Wrap around screen edges
            if bubble["x"] < -bubble["size"]:
                bubble["x"] = WIDTH + bubble["size"]
            elif bubble["x"] > WIDTH + bubble["size"]:
                bubble["x"] = -bubble["size"]
            
            if bubble["y"] < -bubble["size"]:
                bubble["y"] = HEIGHT + bubble["size"]
            elif bubble["y"] > HEIGHT + bubble["size"]:
                bubble["y"] = -bubble["size"]
            
            # Draw bubble with transparency
            bubble_surface = pygame.Surface((bubble["size"]*2, bubble["size"]*2), pygame.SRCALPHA)
            pygame.draw.circle(bubble_surface, bubble["color"] + (bubble["alpha"],), 
                             (bubble["size"], bubble["size"]), bubble["size"])
            screen.blit(bubble_surface, (bubble["x"] - bubble["size"], bubble["y"] - bubble["size"]))
        
        # Draw title with glow effect
        title_font = pygame.font.SysFont('Arial', 60)
        for offset in range(5, 0, -1):
            title_glow = title_font.render("Bubble Shooter", True, (100, 100, 255, 50))
            screen.blit(title_glow, 
                       (WIDTH // 2 - title_glow.get_width() // 2 + offset, 
                        80 + offset))
            screen.blit(title_glow, 
                       (WIDTH // 2 - title_glow.get_width() // 2 - offset, 
                        80 - offset))
        
        title = title_font.render("Bubble Shooter", True, (150, 150, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        
        # Draw subtitle
        subtitle_font = pygame.font.SysFont('Arial', 30)
        subtitle = subtitle_font.render("Powerup Edition", True, (255, 215, 0))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 150))
        
        # Draw simplified instructions - just the essentials
        instructions = [
            "Match 3+ bubbles of the same color",
            "Collect powerups for special abilities",
            "",
            "Press any key to start"
        ]
        
        # Draw powerup icons in a row
        powerup_types = ["bomb", "rainbow", "lightning", "freeze", "magnet", "time_slow", "multi_shot"]
        powerup_colors = {
            "bomb": (255, 50, 50),
            "rainbow": (255, 215, 0),
            "lightning": (100, 100, 255),
            "freeze": (200, 200, 255),
            "magnet": (255, 105, 180),
            "time_slow": (50, 205, 50),
            "multi_shot": (0, 128, 128)
        }
        
        # Create a temporary powerup object for each type to draw
        powerup_y = HEIGHT - 120
        spacing = WIDTH / (len(powerup_types) + 1)
        for i, p_type in enumerate(powerup_types):
            powerup = Powerup(spacing * (i + 1), powerup_y, p_type)
            powerup.draw()
        
        y_pos = 220
        instruction_font = pygame.font.SysFont('Arial', 24)
        for line in instructions:
            text = instruction_font.render(line, True, WHITE)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_pos))
            y_pos += 40
        
        pygame.display.flip()
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False
        
        # Cap the frame rate
        clock.tick(60)

def main():
    game = Game()
    leaderboard = Leaderboard()
    show_instructions()
    
    # For tracking game time
    clock_time = 0
    frame_count = 0
    
    # For entering player name
    entering_name = False
    player_name = ""
    name_cursor_visible = True
    cursor_blink_timer = 0
    
    # For showing leaderboard
    showing_leaderboard = False
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if entering_name:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Save score and exit name entry mode
                        if player_name:
                            leaderboard.add_score(player_name, game.score, game.game_time, game.shots_fired)
                            leaderboard.save()
                            entering_name = False
                            showing_leaderboard = True
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        entering_name = False
                    elif len(player_name) < 15:  # Limit name length
                        if event.unicode.isalnum() or event.unicode in [' ', '_', '-']:
                            player_name += event.unicode
            elif showing_leaderboard:
                if event.type == pygame.KEYDOWN:
                    showing_leaderboard = False
                    game = Game()  # Reset game
            else:
                if event.type == pygame.MOUSEMOTION:
                    if not game.game_over:
                        # Calculate angle based on mouse position
                        mouse_x, mouse_y = event.pos
                        dx = mouse_x - WIDTH // 2
                        dy = SHOOTER_Y - mouse_y
                        angle = math.degrees(math.atan2(dx, dy))
                        
                        # Limit angle
                        game.shooter_angle = max(-MAX_ANGLE, min(MAX_ANGLE, angle))
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not game.game_over and game.shooting_bubble is None:
                        game.shoot_bubble()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and game.game_over:
                        game = Game()
                    # Debug key to spawn powerups (for testing)
                    elif event.key == pygame.K_p and not game.game_over:
                        powerup_type = random.choice(["bomb", "rainbow", "lightning", "freeze", 
                                                    "magnet", "time_slow", "multi_shot"])
                        game.powerups.append(Powerup(WIDTH // 2, HEIGHT // 2, powerup_type))
                    # Use stored powerup
                    elif event.key == pygame.K_SPACE and game.stored_powerup and not game.game_over:
                        game.activate_powerup(game.stored_powerup)
                        game.stored_powerup = None
                    # Save score to leaderboard
                    elif event.key == pygame.K_s and game.game_over:
                        entering_name = True
                        player_name = ""
                    # Show leaderboard
                    elif event.key == pygame.K_l:
                        showing_leaderboard = True
        
        # Update game state
        if not game.game_over and not entering_name and not showing_leaderboard:
            game.update()
            
            # Update game time (every second)
            frame_count += 1
            if frame_count >= 60:  # Assuming 60 FPS
                game.game_time += 1
                frame_count = 0
        
        # Draw everything
        if entering_name:
            # Draw name entry screen
            screen.blit(background, (0, 0))
            
            # Draw prompt
            prompt_font = pygame.font.SysFont('Arial', 36)
            prompt_text = prompt_font.render("Enter Your Name:", True, WHITE)
            screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 100))
            
            # Draw name box
            name_box_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 30, 400, 60)
            pygame.draw.rect(screen, (50, 50, 50), name_box_rect)
            pygame.draw.rect(screen, WHITE, name_box_rect, 2)
            
            # Draw entered name
            name_font = pygame.font.SysFont('Arial', 32)
            name_text = name_font.render(player_name, True, WHITE)
            screen.blit(name_text, (name_box_rect.x + 10, name_box_rect.y + 15))
            
            # Draw blinking cursor
            cursor_blink_timer += 1
            if cursor_blink_timer >= 30:
                name_cursor_visible = not name_cursor_visible
                cursor_blink_timer = 0
                
            if name_cursor_visible:
                cursor_x = name_box_rect.x + 10 + name_text.get_width()
                pygame.draw.line(screen, WHITE, 
                               (cursor_x, name_box_rect.y + 15),
                               (cursor_x, name_box_rect.y + 45), 2)
            
            # Draw instructions
            inst_font = pygame.font.SysFont('Arial', 24)
            inst_text1 = inst_font.render("Press ENTER to save", True, WHITE)
            inst_text2 = inst_font.render("Press ESC to cancel", True, WHITE)
            
            screen.blit(inst_text1, (WIDTH // 2 - inst_text1.get_width() // 2, HEIGHT // 2 + 50))
            screen.blit(inst_text2, (WIDTH // 2 - inst_text2.get_width() // 2, HEIGHT // 2 + 80))
            
        elif showing_leaderboard:
            # Draw leaderboard screen
            leaderboard.draw(screen)
        else:
            game.draw()
        
        pygame.display.flip()
        clock.tick(60)

class Leaderboard:
    def __init__(self):
        self.scores = []
        self.filename = "leaderboard.json"
        self.load()
    
    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.scores = json.load(f)
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
            self.scores = []
    
    def save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.scores, f)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, name, score, game_time, shots):
        # Calculate efficiency
        efficiency = score / max(1, shots)
        
        # Create score entry
        entry = {
            "name": name,
            "score": score,
            "time": game_time,
            "shots": shots,
            "efficiency": efficiency,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self.scores.append(entry)
        
        # Sort by score (descending)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Keep only top 10 scores
        if len(self.scores) > 10:
            self.scores = self.scores[:10]
    
    def draw(self, screen):
        # Draw background
        screen.blit(background, (0, 0))
        
        # Draw title
        title_font = pygame.font.SysFont('Arial', 48)
        title = title_font.render("Leaderboard", True, (150, 150, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw column headers
        header_font = pygame.font.SysFont('Arial', 24)
        headers = ["Rank", "Name", "Score", "Time", "Shots", "Efficiency", "Date"]
        header_widths = [60, 200, 100, 100, 80, 120, 140]
        header_x = 50
        
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, (255, 255, 0))
            screen.blit(header_text, (header_x, 120))
            header_x += header_widths[i]
        
        # Draw horizontal line
        pygame.draw.line(screen, WHITE, (50, 150), (WIDTH - 50, 150), 2)
        
        # Draw scores
        score_font = pygame.font.SysFont('Arial', 20)
        y = 180
        
        if not self.scores:
            no_scores_text = score_font.render("No scores yet! Be the first to set a record!", True, WHITE)
            screen.blit(no_scores_text, (WIDTH // 2 - no_scores_text.get_width() // 2, y))
        else:
            for i, entry in enumerate(self.scores):
                x = 50
                
                # Rank
                rank_text = score_font.render(f"{i+1}", True, WHITE)
                screen.blit(rank_text, (x, y))
                x += header_widths[0]
                
                # Name
                name_text = score_font.render(entry["name"], True, WHITE)
                screen.blit(name_text, (x, y))
                x += header_widths[1]
                
                # Score
                score_text = score_font.render(f"{entry['score']}", True, WHITE)
                screen.blit(score_text, (x, y))
                x += header_widths[2]
                
                # Time
                minutes = entry["time"] // 60
                seconds = entry["time"] % 60
                time_text = score_font.render(f"{minutes}:{seconds:02d}", True, WHITE)
                screen.blit(time_text, (x, y))
                x += header_widths[3]
                
                # Shots
                shots_text = score_font.render(f"{entry['shots']}", True, WHITE)
                screen.blit(shots_text, (x, y))
                x += header_widths[4]
                
                # Efficiency
                eff_text = score_font.render(f"{entry['efficiency']:.1f}", True, WHITE)
                screen.blit(eff_text, (x, y))
                x += header_widths[5]
                
                # Date
                date_text = score_font.render(entry["date"], True, WHITE)
                screen.blit(date_text, (x, y))
                
                y += 40
        
        # Draw instructions
        inst_font = pygame.font.SysFont('Arial', 24)
        inst_text = inst_font.render("Press any key to continue", True, WHITE)
        screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, HEIGHT - 50))

if __name__ == "__main__":
    main()
