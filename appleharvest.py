import random
import pygame
import queue

# Set up the game window
pygame.init()
screen_width = 1024
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Apple Harvest")

# Wall laser
wall_laser_y = 150

# Define some constants
good_apple_color = (0, 255, 0)
bad_apple_color = (255, 0, 0)
lever_color = (0, 0, 255)
laser_color = (200, 0, 0)
apple_radius = 20
lever_width = 100
lever_height = 10
apple_speed = 5
lever_speed = 10
game_duration = 120 # in seconds

max_lever_displacement = 20

# Define some variables
good_apple_count = 0
bad_apple_count = 0

bad_apple_value = -3
good_apple_value = 1
score = 0
game_start_time = pygame.time.get_ticks()

# Define some functions
def draw_laser_scan(x_pos, obstacle_height=0):
    pygame.draw.rect(screen, laser_color, (x_pos + lever_width/2, obstacle_height, 1, screen_height))  

def draw_side_laser_sensor(y_pos):
    pygame.draw.rect(screen, lever_color, (0, y_pos - 5, 5, 10))

def draw_lever(x_pos):
    pygame.draw.rect(screen, lever_color, (x_pos, screen_height - lever_height, lever_width, lever_height))

def draw_apple(x_pos, y_pos, color):
    pygame.draw.circle(screen, color, (x_pos, y_pos), apple_radius)

def generate_apple():
    x_pos = random.randint(apple_radius, screen_width - apple_radius)
    y_pos = 0
    if random.random() < 0.2: # 20% chance of generating a bad apple
        color = bad_apple_color
    else:
        color = good_apple_color
    return (x_pos, y_pos, color)

def detect_collision(apple, lever_pos):
    x_pos, y_pos, color = apple
    if y_pos + apple_radius >= screen_height - lever_height and x_pos >= lever_pos and x_pos <= lever_pos + lever_width:
        return True
    else:
        return False


def find_apple_in_laser_range(x_pos, apples):
    closest_apple = None
    lever_center = x_pos + lever_width/2
    for apple in apples:
      # Choose closest in height
      if abs(apple[0] - lever_center) < apple_radius:
        closest_apple = max(closest_apple, apple, key=lambda a: 0 if a is None else a[1]) 

    return closest_apple

# Define some functions
def draw_wall_laser_scan(y_pos, obstacle_dist=screen_width):
    pygame.draw.rect(screen, laser_color, (0, y_pos, obstacle_dist, 1))

def find_apple_in_side_laser_range(y_pos, apples):
    closest_apple = None
    side_laser_center = y_pos
    for apple in apples:
      # Choose closest in height
      if abs(apple[1] - side_laser_center) < apple_radius:
        closest_apple = max(closest_apple, apple, key=lambda a: 0 if a is None else a[1]) 

    return closest_apple

########################################################################
# 
# 
# Your code goes in this section below
# Avoid acessing global variables.
# 
########################################################################

# World model should contain data and methods 
# to represent and predict how the world works
class WorldModel:
    def __init__(self):
        self.apples_know = [] # Lista de macas existentes

    def update_apples(self, apples):
        self.apples_know = apples

    def get_closest_apple(self, lever_pos):
        if not self.apples_know:
            return None, None, None


        apple_sorted_y = sorted(self.apples_know, key=lambda apple: abs(600 - apple[1]))[0] # apple_x, apple_y, color
        apple_sorted_x = sorted(self.apples_know, key=lambda apple: abs(apple[0] - lever_pos))[0] # apple_x, apple_y, color

        return  apple_sorted_y, apple_sorted_x, self.apples_know

# Agent contains its reaction based on sensors and its understanding
# of the world. This is where you decide what action you take
class Agent:
  def __init__(self, wm, max_lever_displacement, arena_width):
    self.worlmodel = wm
    self.max_lever_displacement = max_lever_displacement 
    self.arena_width = arena_width
    self.last_time_apple = 0

  def decision(self, lever_pos, laser_scan, side_laser_scan, score):
    print(f"{lever_pos=}, {laser_scan=}, {side_laser_scan=}, {score=}, {self.max_lever_displacement=}, {self.arena_width=}, {lever_width=}")
    closest_apple_y, closest_apple_x, apples = wm.get_closest_apple(lever_pos)


    if not closest_apple_y:
        return lever_pos

    apple_x, apple_y, apple_color = closest_apple_y
    apple_time_fall = apple_y / apple_speed
    lever_time_catch_apple = abs(apple_x - lever_pos) / lever_speed
    quadrants = [0,0]

    for x in apples:
        if x[2] == good_apple_color:
            if x[0] < screen_width/2:
                quadrants[0] += 1
            else:
                quadrants[1] += 1

    apple_secundaria = sorted(apples, key=lambda apple: abs(600 - apple[1]))[0] # apple_x, apple_y, color
    # difference_time = abs(apple_time_fall - self.last_time_apple)
    # self.last_time_apple = apple_time_fall


    if apple_color == bad_apple_color and (((apple_x - 10) >= (lever_pos - 50) or (apple_x - 10) <= (lever_pos + 50)) or ((apple_x + 10) >= (lever_pos - 50) or (apple_x + 10) <= (lever_pos + 50))):
        print("VO ME SAIR")
        if apple_x > lever_pos:
            return max(lever_pos + self.max_lever_displacement, self.arena_width - lever_width)
        else:
            return min(lever_pos - self.max_lever_displacement, 0)
    elif apple_color == good_apple_color and apple_time_fall >= lever_time_catch_apple: 
        if apple_x > lever_pos:
            return min(lever_pos + self.max_lever_displacement, self.arena_width - lever_width)
        else:
            return max(lever_pos - self.max_lever_displacement, 0)
    else:
        if apple_secundaria[2] == good_apple_color: 
            if apple_secundaria[0] > lever_pos:
                return min(lever_pos + self.max_lever_displacement, self.arena_width - lever_width)
            else:
                return max(lever_pos - self.max_lever_displacement, 0)
        return lever_pos

########################################################################
# 
# 
# Main game loop
# 
# 
########################################################################

wm = WorldModel()
agent = Agent(wm, max_lever_displacement, screen_width)

running = True
apples = []
lever_pos = screen_width / 2
closest_apple = None
closest_s_apple = None
decisions_count = 0

good_apple_caught = 0
bad_apple_caught = 0

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill((255, 255, 255))

    closest_apple_distance = None
    if closest_apple is not None:
      closest_apple_distance = {
        "distance": (screen_height - lever_height) - closest_apple[1] - apple_radius,
        "color": "red" if closest_apple[2] == (255, 0, 0) else "green"
      }

    closest_side_apple_distance = None
    if closest_s_apple is not None:
      closest_side_apple_distance = {
        "distance": (closest_s_apple[0]) - apple_radius,
        "color": "red" if closest_s_apple[2] == (255, 0, 0) else "green"
      }      

    #print(f"{closest_apple_distance=} with data {closest_apple=}")  
    desired_lever_pos = agent.decision(lever_pos, closest_apple_distance, closest_side_apple_distance, score)

    if abs(lever_pos - desired_lever_pos) > lever_width/2 + max_lever_displacement:
        print("Max lever displacement exceeded")
    else: 
        lever_pos = desired_lever_pos

    closest_apple = find_apple_in_laser_range(lever_pos, apples)
    closest_s_apple = find_apple_in_side_laser_range(wall_laser_y, apples)

    # Draw the lever    
    draw_lever(lever_pos)
    draw_laser_scan(lever_pos, 0 if closest_apple is None else closest_apple[1])
    draw_wall_laser_scan(wall_laser_y,  screen_width if closest_s_apple is None else closest_s_apple[0])
    draw_side_laser_sensor(wall_laser_y)

    # Generate apples
    if random.random() < 0.05: # 5% chance of generating an apple in each frame
        apple = generate_apple()
        if apple[2] == good_apple_color:
            good_apple_count += 1
        else:
            bad_apple_count += 1
        apples.append(apple)

    # Move apples and detect collisions
    novel_apples = []
    for idx,apple in enumerate(apples):
        x_pos, y_pos, color = apple
        y_pos += apple_speed
        if detect_collision(apple, lever_pos):
            if color == good_apple_color:
                score += good_apple_value
                good_apple_caught += 1
            else:
                score += bad_apple_value
                bad_apple_caught += 1
        elif y_pos >= screen_height: 
            pass
        else:
            novel_apples.append((x_pos, y_pos, color))
            draw_apple(x_pos, y_pos, color)
    apples = novel_apples


    wm.update_apples(apples)

    # Draw the score
    score_text = "Score: " + str(score)
    font = pygame.font.SysFont("Arial", 32)
    score_surface = font.render(score_text, True, (0, 0, 0))
    screen.blit(score_surface, (10, 10))

    # Check if the game is over
    elapsed_time = (pygame.time.get_ticks() - game_start_time) / 1000
    #if elapsed_time >= game_duration:
    #    running = False

    decisions_count += 1  
    if decisions_count >= 3441: # Aproximadamente dois minutos
      running = False

    time_surface = font.render("Time (s): " + str(elapsed_time), True, (0, 0, 0))
    screen.blit(time_surface, (200, 10))

    # Update the display
    pygame.display.update()
    pygame.time.wait(int(1000/30))
    #pygame.time.wait(500)


print(f"Number of decisions {decisions_count}")

# Show the final score
final_score_text = "Final score: " + str(score)
print(f"score: {score}")
font = pygame.font.SysFont("Arial", 64)
final_score_surface = font.render(final_score_text, True, (0, 0, 0))
final_score_rect = final_score_surface.get_rect(center=(screen_width/2, screen_height/2))
screen.blit(final_score_surface, final_score_rect)
pygame.display.update()

# Wait for a few seconds before quitting
pygame.time.wait(3000)

print("Good_apple count: ")
print(good_apple_count)

print("Bad_apple count: ")
print(bad_apple_count)

print("Good_apple_caught: ")
print(good_apple_caught)

print("Bad_apple_caught: ")
print(bad_apple_caught)

# Quit the game
pygame.quit()  
