import pygame
import random
import math
import colorsys

# --- Settings ---
WIDTH, HEIGHT = 800, 600
NUM_BOIDS = 500
NUM_PREDATORS = 0
MAX_SPEED = 4
NEIGHBOR_RADIUS = 50
SEPARATION_RADIUS = 5
MOUSE_REPEL_RADIUS = 100
PREDATOR_CHASE_RADIUS = 150
TRAIL_FADE = 55
PREDATOR_SPEED = 2.5
BOID_SIZE = 2  # half-length of triangle
PREDATOR_SIZE = BOID_SIZE * 2  # predators are 2x bigger

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boids with Predators (Outlined)")
clock = pygame.time.Clock()

# Trail surface
trail_surface = pygame.Surface((WIDTH, HEIGHT))
trail_surface.set_alpha(TRAIL_FADE)
trail_surface.fill((0, 0, 0))


# --- Boid Class ---
class Boid:
    def __init__(self):
        self.pos = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * MAX_SPEED

    def update(self, boids, mouse_pos, predators):
        alignment = pygame.Vector2(0, 0)
        cohesion = pygame.Vector2(0, 0)
        separation = pygame.Vector2(0, 0)
        total = 0

        for other in boids:
            if other == self:
                continue
            distance = self.pos.distance_to(other.pos)
            if distance < NEIGHBOR_RADIUS:
                alignment += other.vel
                cohesion += other.pos
                total += 1
            if distance < SEPARATION_RADIUS:
                separation -= other.pos - self.pos

        if total > 0:
            alignment /= total
            alignment = alignment.normalize() * MAX_SPEED
            cohesion /= total
            cohesion = (cohesion - self.pos).normalize() * MAX_SPEED

        # Mouse avoidance
        mouse_vec = self.pos - pygame.Vector2(mouse_pos)
        mouse_dist = mouse_vec.length()
        if mouse_dist < MOUSE_REPEL_RADIUS and mouse_dist > 0:
            separation += mouse_vec.normalize() * (MOUSE_REPEL_RADIUS / mouse_dist)

        # Flee from predators
        for predator in predators:
            vec = self.pos - predator.pos
            dist = vec.length()
            if dist < PREDATOR_CHASE_RADIUS and dist > 0:
                separation += vec.normalize() * (PREDATOR_CHASE_RADIUS / dist) * 1.5

        # Update velocity
        self.vel += alignment * 0.05 + cohesion * 0.01 + separation * 0.1

        # Limit speed
        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

        # Move
        self.pos += self.vel

        # Wrap around screen
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        if self.pos.y > HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT

    def draw(self, surface):
        angle = self.vel.angle_to(pygame.Vector2(1, 0))
        hue = (angle % 360) / 360
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        color = (int(r * 255), int(g * 255), int(b * 255))

        points = [
            self.pos + pygame.Vector2(BOID_SIZE, 0).rotate(-angle),
            self.pos + pygame.Vector2(-BOID_SIZE / 2, BOID_SIZE / 2).rotate(-angle),
            self.pos + pygame.Vector2(-BOID_SIZE / 2, -BOID_SIZE / 2).rotate(-angle),
        ]
        pygame.draw.polygon(surface, color, points)


# --- Predator Class ---
class Predator:
    def __init__(self):
        self.pos = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * PREDATOR_SPEED
        self.acceleration = pygame.Vector2(0, 0)
        self.max_speed = PREDATOR_SPEED
        self.max_force = 0.1  # steering smoothness
        self.separation_radius = 40  # predators avoid each other

    def update(self, predators, boids):
        # Boid-like behavior
        alignment = pygame.Vector2(0, 0)
        separation = pygame.Vector2(0, 0)
        cohesion = pygame.Vector2(0, 0)
        total = 0

        for other in predators:
            if other == self:
                continue
            distance = self.pos.distance_to(other.pos)
            if distance < self.separation_radius:
                separation -= other.pos - self.pos
            if distance < NEIGHBOR_RADIUS:
                alignment += other.vel
                cohesion += other.pos
                total += 1

        if total > 0:
            alignment /= total
            alignment = alignment.normalize() * self.max_speed
            cohesion /= total
            cohesion = (cohesion - self.pos).normalize() * self.max_speed

        # Chase nearest boid
        if boids:
            closest = min(boids, key=lambda b: self.pos.distance_to(b.pos))
            chase = (closest.pos - self.pos).normalize() * self.max_speed
        else:
            chase = pygame.Vector2(0, 0)

        # Combine behaviors
        self.acceleration = (
            alignment * 0.05 + cohesion * 0.01 + separation * 0.2 + chase * 0.2
        )

        # Apply velocity and update position
        self.vel += self.acceleration
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self.pos += self.vel

        # Wrap around screen
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        if self.pos.y > HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT

    def draw(self, surface):
        angle = self.vel.angle_to(pygame.Vector2(1, 0))
        points = [
            self.pos + pygame.Vector2(PREDATOR_SIZE, 0).rotate(-angle),
            self.pos
            + pygame.Vector2(-PREDATOR_SIZE / 2, PREDATOR_SIZE / 2).rotate(-angle),
            self.pos
            + pygame.Vector2(-PREDATOR_SIZE / 2, -PREDATOR_SIZE / 2).rotate(-angle),
        ]
        pygame.draw.polygon(surface, (255, 255, 255), points)


# --- Create Boids and Predators ---
boids = [Boid() for _ in range(NUM_BOIDS)]
predators = [Predator() for _ in range(NUM_PREDATORS)]

# --- Main Loop ---
running = True
while running:
    clock.tick(60)
    screen.blit(trail_surface, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for boid in boids:
        boid.update(boids, mouse_pos, predators)
        boid.draw(screen)

    for predator in predators:
        predator.update(predators, boids)
        predator.draw(screen)

    pygame.display.flip()

pygame.quit()
