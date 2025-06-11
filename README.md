# Enhanced Puzzle Bobble

A visually appealing bubble-matching puzzle game with special effects and animations.

## Requirements

- Python 3.x
- Pygame

## Installation

Before running the game, make sure you have Pygame installed:

```bash
pip install pygame
```

## How to Play

1. Run the game:
   ```bash
   python puzzle_bobble_enhanced.py
   ```

2. Game Rules:
   - Aim and shoot colored bubbles to match groups of three or more of the same color
   - Matching bubbles will pop and disappear with explosion effects
   - Bubbles that are no longer connected to the top will fall
   - The game ends if bubbles reach the bottom of the screen

3. Controls:
   - Move mouse to aim the shooter
   - Left-click to shoot a bubble
   - R key to restart the game (after game over)

4. Scoring:
   - 10 points for each bubble popped in a match
   - 5 points for each floating bubble that falls
   - Combo multiplier for consecutive matches
   - Score popups show points earned

## Visual Features

- Gradient bubble colors with shine effects
- Starry space background
- Particle effects when bubbles pop
- Explosion animations
- Score popups
- Aiming guide line
- Combo counter
- Text shadows and glow effects
- Animated game over screen

## Sound Effects (Optional)

The game will attempt to load sound effects from a "sounds" folder. If the sounds can't be loaded, the game will continue without sound. If you want sound effects, create a "sounds" folder in the same directory as the game and add these WAV files:
- shoot.wav
- pop.wav
- fall.wav
- game_over.wav

## Strategy Tips

- Try to create chains of floating bubbles for bonus points
- Build up combos by making consecutive matches
- Focus on clearing bubbles from the bottom to prevent game over
- Look for opportunities to create large matches
