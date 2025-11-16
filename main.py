import pygame
import numpy as np
import math
import time
import json
import os
from datetime import datetime

# Initialize pygame
pygame.init()

# Settings
SAMPLE_RATE = 44100
BIT_DEPTH = 16
BUFFER_SIZE = 1024

# Create window
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("CHIPTONE")
clock = pygame.time.Clock()

# Sound init
pygame.mixer.init(SAMPLE_RATE, -BIT_DEPTH, 2, BUFFER_SIZE)

# Colors
BACKGROUND = (10, 15, 25)
PANEL_DARK = (20, 25, 40)
PANEL_LIGHT = (30, 35, 55)
NEON_BLUE = (0, 200, 255)
NEON_PURPLE = (180, 70, 255)
NEON_GREEN = (0, 255, 150)
NEON_RED = (255, 50, 100)
NEON_YELLOW = (255, 220, 0)
TEXT_LIGHT = (220, 220, 240)
TEXT_DIM = (150, 160, 180)

class Synth:
    def __init__(self):
        self.frequency = 440
        self.waveform = 'sine'
        self.volume = 0.5
        self.playing = False
        self.sound = None
        self.current_note = None
        self.wave_points = []
        self.effects = {
            'distortion': False,
            'delay': False,
            'low_pass': False,
            'bit_crush': True
        }
        self.delay_time = 0.3
        self.distortion_amount = 2.0
        self.bit_crush_factor = 4
        
    def generate_sample(self, length):
        """Generate sound sample with 8-bit emulation"""
        t = np.linspace(0, length, int(SAMPLE_RATE * length))
        
        # Generate base waveform
        if self.waveform == 'sine':
            wave = np.sin(2 * np.pi * self.frequency * t)
        elif self.waveform == 'square':
            wave = np.sign(np.sin(2 * np.pi * self.frequency * t))
        elif self.waveform == 'sawtooth':
            wave = 2 * (t * self.frequency - np.floor(0.5 + t * self.frequency))
        elif self.waveform == 'triangle':
            wave = 2 * np.abs(2 * (t * self.frequency - np.floor(t * self.frequency + 0.5))) - 1
        else:
            wave = np.sin(2 * np.pi * self.frequency * t)
        
        # Apply effects
        if self.effects['distortion']:
            wave = np.tanh(wave * self.distortion_amount)
            
        if self.effects['bit_crush']:
            levels = 2 ** self.bit_crush_factor
            wave = np.round(wave * levels) / levels
            
        if self.effects['low_pass']:
            alpha = 0.1
            filtered = np.zeros_like(wave)
            filtered[0] = wave[0]
            for i in range(1, len(wave)):
                filtered[i] = alpha * wave[i] + (1 - alpha) * filtered[i-1]
            wave = filtered
        
        # Apply volume
        wave = wave * self.volume
        
        # Store wave points for visualization
        self.wave_points = (wave[:300] * 32767).astype(np.int16)
        
        # Convert to 16-bit for Pygame compatibility
        wave_16bit = (wave * 32767).astype(np.int16)
        
        # Create stereo sound
        stereo_wave = np.column_stack((wave_16bit, wave_16bit))
        
        # Apply delay effect
        if self.effects['delay']:
            delay_samples = int(SAMPLE_RATE * self.delay_time)
            if len(stereo_wave) > delay_samples:
                delayed = np.roll(stereo_wave, delay_samples, axis=0)
                delayed[:delay_samples] = 0
                stereo_wave = stereo_wave + (delayed * 0.5).astype(np.int16)
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def play_note(self, freq, note_name, waveform='sine', duration=1.0):
        """Play note"""
        self.frequency = freq
        self.waveform = waveform
        self.current_note = note_name
        self.sound = self.generate_sample(duration)
        self.sound.play()
        self.playing = True
    
    def stop(self):
        """Stop playback"""
        if self.sound:
            self.sound.stop()
        self.playing = False
        self.current_note = None

class Recorder:
    def __init__(self):
        self.recording = False
        self.record_start_time = 0
        self.recorded_notes = []
        self.recordings_folder = "recordings"
        self.ensure_recordings_folder()
        
    def ensure_recordings_folder(self):
        """Create recordings folder if it doesn't exist"""
        if not os.path.exists(self.recordings_folder):
            os.makedirs(self.recordings_folder)
        
    def start_recording(self):
        """Start recording"""
        self.recording = True
        self.record_start_time = time.time()
        self.recorded_notes = []
        
    def stop_recording(self):
        """Stop recording"""
        self.recording = False
        
    def add_note(self, note_name, frequency, waveform):
        """Add note to recording"""
        if self.recording:
            timestamp = time.time() - self.record_start_time
            self.recorded_notes.append({
                'time': round(timestamp, 2),
                'note': note_name,
                'freq': frequency,
                'wave': waveform
            })
    
    def save_recording(self):
        """Save recording to JSON file"""
        if not self.recorded_notes:
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.json"
        filepath = os.path.join(self.recordings_folder, filename)
        
        recording_data = {
            'timestamp': timestamp,
            'duration': round(time.time() - self.record_start_time, 2),
            'total_notes': len(self.recorded_notes),
            'notes': self.recorded_notes
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(recording_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving recording: {e}")
            return False
    
    def load_recording(self, filename):
        """Load recording from JSON file"""
        filepath = os.path.join(self.recordings_folder, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading recording: {e}")
            return None

# Create synth and recorder
synth = Synth()
recorder = Recorder()

# Piano keys
keys = [
    {'key': pygame.K_a, 'note': 'C', 'freq': 261.63, 'color': NEON_BLUE, 'pos': (100, 500)},
    {'key': pygame.K_w, 'note': 'C#', 'freq': 277.18, 'color': NEON_PURPLE, 'pos': (135, 500)},
    {'key': pygame.K_s, 'note': 'D', 'freq': 293.66, 'color': NEON_BLUE, 'pos': (170, 500)},
    {'key': pygame.K_e, 'note': 'D#', 'freq': 311.13, 'color': NEON_PURPLE, 'pos': (205, 500)},
    {'key': pygame.K_d, 'note': 'E', 'freq': 329.63, 'color': NEON_BLUE, 'pos': (240, 500)},
    {'key': pygame.K_f, 'note': 'F', 'freq': 349.23, 'color': NEON_GREEN, 'pos': (275, 500)},
    {'key': pygame.K_t, 'note': 'F#', 'freq': 369.99, 'color': NEON_PURPLE, 'pos': (310, 500)},
    {'key': pygame.K_g, 'note': 'G', 'freq': 392.00, 'color': NEON_GREEN, 'pos': (345, 500)},
    {'key': pygame.K_y, 'note': 'G#', 'freq': 415.30, 'color': NEON_PURPLE, 'pos': (380, 500)},
    {'key': pygame.K_h, 'note': 'A', 'freq': 440.00, 'color': NEON_RED, 'pos': (415, 500)},
    {'key': pygame.K_u, 'note': 'A#', 'freq': 466.16, 'color': NEON_PURPLE, 'pos': (450, 500)},
    {'key': pygame.K_j, 'note': 'B', 'freq': 493.88, 'color': NEON_RED, 'pos': (485, 500)},
    {'key': pygame.K_k, 'note': 'C5', 'freq': 523.25, 'color': NEON_YELLOW, 'pos': (520, 500)}
]

# Waveforms with colors
waveforms = [
    {'name': 'sine', 'color': NEON_BLUE},
    {'name': 'square', 'color': NEON_GREEN},
    {'name': 'sawtooth', 'color': NEON_RED},
    {'name': 'triangle', 'color': NEON_YELLOW}
]
current_waveform = 0

# Effect pedals
pedals = [
    {'key': pygame.K_1, 'name': 'DISTORTION', 'effect': 'distortion', 'color': NEON_RED},
    {'key': pygame.K_2, 'name': 'DELAY', 'effect': 'delay', 'color': NEON_PURPLE},
    {'key': pygame.K_3, 'name': 'LOW PASS', 'effect': 'low_pass', 'color': NEON_BLUE},
    {'key': pygame.K_4, 'name': 'BIT CRUSH', 'effect': 'bit_crush', 'color': NEON_GREEN}
]

# Animation variables
wave_animation_offset = 0
note_animation_alpha = 0
particles = []
save_message_time = 0

def create_particle(x, y, color):
    """Create visual particles"""
    return {
        'x': x, 'y': y,
        'color': color,
        'size': np.random.randint(2, 6),
        'speed_x': np.random.uniform(-2, 2),
        'speed_y': np.random.uniform(-3, 0),
        'life': 1.0
    }

def draw_rounded_rect(surface, color, rect, radius, alpha=255):
    """Draw rounded rectangle"""
    x, y, width, height = rect
    
    # Create temporary surface for alpha
    temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw rounded rect on temp surface
    if alpha == 255:
        pygame.draw.rect(temp_surface, color, (0, 0, width, height), border_radius=radius)
    else:
        r, g, b = color
        pygame.draw.rect(temp_surface, (r, g, b, alpha), (0, 0, width, height), border_radius=radius)
    
    # Blit to main surface
    surface.blit(temp_surface, (x, y))

def draw_glowing_circle(surface, color, pos, radius, glow_size=10):
    """Draw circle with glow effect"""
    # Create temporary surface for glow
    size = radius * 2 + glow_size * 2
    temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (radius + glow_size, radius + glow_size)
    
    # Draw glow layers
    for r in range(glow_size, 0, -1):
        alpha = 50 - r * (50 // glow_size)
        pygame.draw.circle(temp_surface, (*color, alpha), center, radius + r)
    
    # Draw main circle
    pygame.draw.circle(temp_surface, (*color, 255), center, radius)
    
    surface.blit(temp_surface, (pos[0] - radius - glow_size, pos[1] - radius - glow_size))

def draw_wave_visualization(surface, wave_points, x, y, width, height):
    """Draw modern waveform visualization"""
    if len(wave_points) == 0:
        # Draw empty state
        draw_rounded_rect(surface, PANEL_LIGHT, (x, y, width, height), 15)
        pygame.draw.rect(surface, NEON_BLUE, (x, y, width, height), 2, border_radius=15)
        
        font = pygame.font.Font(None, 24)
        text = font.render("Play notes to see waveform", True, TEXT_DIM)
        surface.blit(text, (x + width//2 - text.get_width()//2, y + height//2 - text.get_height()//2))
        return
        
    # Draw background panel
    draw_rounded_rect(surface, PANEL_LIGHT, (x, y, width, height), 15)
    
    # Draw border
    pygame.draw.rect(surface, NEON_BLUE, (x, y, width, height), 2, border_radius=15)
    
    # Draw waveform
    global wave_animation_offset
    wave_animation_offset = (wave_animation_offset + 2) % len(wave_points)
    
    points = []
    for i in range(width):
        idx = (i + wave_animation_offset) % len(wave_points)
        value = wave_points[idx]
        normalized_y = y + height//2 + (value / 32767) * (height//2 - 20)
        points.append((x + i, normalized_y))
    
    if len(points) > 1:
        # Draw main waveform
        for i in range(len(points) - 1):
            pygame.draw.line(surface, NEON_BLUE, points[i], points[i+1], 3)

def draw_piano(surface, keys, current_note):
    """Draw modern piano keyboard"""
    # Draw keyboard background
    draw_rounded_rect(surface, PANEL_DARK, (80, 480, 500, 150), 10)
    
    # Draw keyboard title
    font = pygame.font.Font(None, 24)
    title = font.render("KEYBOARD", True, NEON_YELLOW)
    surface.blit(title, (80 + 250 - title.get_width()//2, 450))
    
    for key in keys:
        x, y = key['pos']
        base_color = key['color']
        
        # Calculate brightness based on whether key is pressed
        if current_note == key['note']:
            color = tuple(min(c + 100, 255) for c in base_color)
            glow_color = base_color
        else:
            color = tuple(max(c - 80, 0) for c in base_color)
            glow_color = tuple(max(c - 120, 0) for c in base_color)
        
        # Draw key with glow if pressed
        key_rect = (x, y, 30, 80)
        draw_rounded_rect(surface, color, key_rect, 5)
        
        if current_note == key['note']:
            pygame.draw.rect(surface, glow_color, key_rect, 2, border_radius=5)
            
            # Add particles
            if np.random.random() < 0.3:
                particles.append(create_particle(x + 15, y, base_color))
        
        # Draw note label
        font = pygame.font.Font(None, 20)
        text = font.render(key['note'], True, TEXT_LIGHT)
        surface.blit(text, (x + 8, y + 85))

def draw_effects_pedals(surface, pedals, synth):
    """Draw modern effect pedals"""
    # Draw effects panel
    draw_rounded_rect(surface, PANEL_LIGHT, (650, 80, 300, 200), 15)
    
    # Title
    title_font = pygame.font.Font(None, 28)
    title = title_font.render("EFFECTS PEDALS", True, NEON_PURPLE)
    surface.blit(title, (800 - title.get_width()//2, 95))
    
    for i, pedal in enumerate(pedals):
        x, y = 680, 140 + i * 45
        active = synth.effects[pedal['effect']]
        
        # Draw pedal background
        pedal_color = PANEL_DARK
        draw_rounded_rect(surface, pedal_color, (x, y, 240, 35), 8)
        
        # Draw active state indicator
        indicator_color = pedal['color'] if active else (80, 80, 100)
        pygame.draw.circle(surface, indicator_color, (x + 20, y + 18), 8)
        if active:
            draw_glowing_circle(surface, pedal['color'], (x + 20, y + 18), 4)
        
        # Draw pedal text
        font = pygame.font.Font(None, 22)
        text_color = pedal['color'] if active else TEXT_DIM
        text = font.render(f"{pedal['name']} [{pedal['key'] - pygame.K_0}]", True, text_color)
        surface.blit(text, (x + 40, y + 8))

def draw_waveform_selector(surface, waveforms, current):
    """Draw waveform selector"""
    # Draw panel
    draw_rounded_rect(surface, PANEL_LIGHT, (650, 300, 300, 120), 15)
    
    # Title
    title_font = pygame.font.Font(None, 28)
    title = title_font.render("WAVEFORM", True, NEON_GREEN)
    surface.blit(title, (800 - title.get_width()//2, 315))
    
    # Draw waveform buttons
    for i, wave in enumerate(waveforms):
        x, y = 670 + i * 70, 350
        is_active = (i == current)
        
        # Button background
        button_color = wave['color'] if is_active else PANEL_DARK
        draw_rounded_rect(surface, button_color, (x, y, 60, 40), 8)
        
        # Button text
        font = pygame.font.Font(None, 20)
        text_color = BACKGROUND if is_active else TEXT_LIGHT
        text = font.render(wave['name'].upper(), True, text_color)
        surface.blit(text, (x + 30 - text.get_width()//2, y + 20 - text.get_height()//2))

def draw_recording_status(surface, recorder, save_message_time):
    """Draw modern recording status"""
    # Draw panel
    draw_rounded_rect(surface, PANEL_LIGHT, (650, 440, 300, 120), 15)
    
    # Show save message if recently saved
    current_time = time.time()
    if current_time - save_message_time < 3:
        font = pygame.font.Font(None, 24)
        text = font.render("Recording Saved!", True, NEON_GREEN)
        surface.blit(text, (800 - text.get_width()//2, 445))
    
    if recorder.recording:
        # Blinking recording indicator
        if int(time.time() * 2) % 2 == 0:
            draw_glowing_circle(surface, NEON_RED, (670, 490), 6)
        
        # Recording text
        font = pygame.font.Font(None, 28)
        text = font.render("RECORDING", True, NEON_RED)
        surface.blit(text, (690, 485))
        
        # Recorded notes count
        count_font = pygame.font.Font(None, 22)
        count_text = count_font.render(f"Notes: {len(recorder.recorded_notes)}", True, TEXT_LIGHT)
        surface.blit(count_text, (690, 515))
        
        # Save hint
        hint_font = pygame.font.Font(None, 18)
        hint_text = hint_font.render("Press S to save", True, TEXT_DIM)
        surface.blit(hint_text, (690, 535))
    else:
        if recorder.recorded_notes:
            font = pygame.font.Font(None, 24)
            text = font.render(f"Ready to record ({len(recorder.recorded_notes)} notes)", True, NEON_GREEN)
            surface.blit(text, (800 - text.get_width()//2, 485))
            
            hint_font = pygame.font.Font(None, 18)
            hint_text = hint_font.render("Press R to record, S to save", True, TEXT_DIM)
            surface.blit(hint_text, (800 - hint_text.get_width()//2, 515))
        else:
            font = pygame.font.Font(None, 24)
            text = font.render("Press R to start recording", True, TEXT_DIM)
            surface.blit(text, (800 - text.get_width()//2, 490))

def draw_note_display(surface, current_note):
    """Draw modern note display"""
    global note_animation_alpha
    
    if current_note:
        note_animation_alpha = min(255, note_animation_alpha + 15)
    else:
        note_animation_alpha = max(0, note_animation_alpha - 8)
    
    # Draw note display panel
    draw_rounded_rect(surface, PANEL_LIGHT, (100, 80, 400, 120), 20)
    
    # Title
    font = pygame.font.Font(None, 28)
    title = font.render("CURRENT NOTE", True, NEON_YELLOW)
    surface.blit(title, (300 - title.get_width()//2, 95))
    
    if note_animation_alpha > 0 and current_note:
        # Draw note text
        font = pygame.font.Font(None, 80)
        text_surface = font.render(current_note, True, NEON_YELLOW)
        text_surface.set_alpha(note_animation_alpha)
        surface.blit(text_surface, (300 - text_surface.get_width()//2, 140 - text_surface.get_height()//2))

def draw_particles(surface):
    """Draw and update particles"""
    global particles
    
    for particle in particles[:]:
        particle['x'] += particle['speed_x']
        particle['y'] += particle['speed_y']
        particle['life'] -= 0.02
        
        if particle['life'] <= 0:
            particles.remove(particle)
        else:
            # Calculate particle properties
            x, y = int(particle['x']), int(particle['y'])
            size = max(1, int(particle['size'] * particle['life']))
            alpha = int(255 * particle['life'])
            
            # Create color with alpha
            r, g, b = particle['color']
            color_with_alpha = (r, g, b, alpha)
            
            # Draw particle
            temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, color_with_alpha, (size, size), size)
            surface.blit(temp_surface, (x - size, y - size))

# Main loop
running = True
while running:
    screen.fill(BACKGROUND)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # Piano keys
            for key_info in keys:
                if event.key == key_info['key']:
                    synth.play_note(key_info['freq'], key_info['note'], 
                                  waveforms[current_waveform]['name'], 1.0)
                    if recorder.recording:
                        recorder.add_note(key_info['note'], key_info['freq'], 
                                        waveforms[current_waveform]['name'])
                    break
            
            # Waveform change
            if event.key == pygame.K_SPACE:
                current_waveform = (current_waveform + 1) % len(waveforms)
            
            # Effect pedals
            for pedal in pedals:
                if event.key == pedal['key']:
                    synth.effects[pedal['effect']] = not synth.effects[pedal['effect']]
            
            # Recording controls
            if event.key == pygame.K_r:
                if recorder.recording:
                    recorder.stop_recording()
                else:
                    recorder.start_recording()
            
            # Save recording
            if event.key == pygame.K_s:
                if recorder.recorded_notes and not recorder.recording:
                    if recorder.save_recording():
                        save_message_time = time.time()
            
            # Exit
            elif event.key == pygame.K_ESCAPE:
                running = False
    
    # Draw interface components
    draw_note_display(screen, synth.current_note)
    draw_wave_visualization(screen, synth.wave_points, 100, 220, 400, 120)
    draw_piano(screen, keys, synth.current_note)
    draw_effects_pedals(screen, pedals, synth)
    draw_waveform_selector(screen, waveforms, current_waveform)
    draw_recording_status(screen, recorder, save_message_time)
    draw_particles(screen)
    
    # Draw instructions panel
    draw_rounded_rect(screen, PANEL_DARK, (50, 650, 900, 40), 8)
    instructions = [
        "A S D F G H J K  -  NOTES",
        "W E T Y U  -  SHARPS", 
        "SPACE  -  WAVEFORM",
        "1-4  -  EFFECTS",
        "R  -  RECORD/STOP",
        "S  -  SAVE",
        "ESC  -  EXIT"
    ]
    
    font = pygame.font.Font(None, 20)
    x_pos = 70
    for i, line in enumerate(instructions):
        text = font.render(line, True, TEXT_DIM)
        screen.blit(text, (x_pos, 665))
        x_pos += text.get_width() + 30
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()