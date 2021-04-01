from math import ceil, floor, nan, sqrt
import pygame
import ctypes
from random import uniform, seed
from sys import exit
from time import time_ns
from pygame.constants import (
    KEYDOWN,
    K_ESCAPE,
    QUIT,
)

# [NOTE] Handle exceptions more properly

# Seeding the random number generater with the current time in nano-seconds
seed(time_ns())

# Extracting size (width, height) of the current window / screen
user32 = ctypes.windll.user32
WIN_W, WIN_H = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Soccer pitch dimensions
PITCH_W = 68
PITCH_H = 105
PENALTY_AREA_W = 40.3
PENALTY_AREA_H = 16.5
GOAL_AREA_W = 18.32
GOAL_AREA_H = 5.5
CENTER_SPOT_R = 9.15
BOUNDARY_W = 5

# Expanding to fit in the window
EXPANSION_FACTOR = int(
    min(
        ((WIN_W - (2 * BOUNDARY_W)) / PITCH_W),
        ((WIN_H - (2 * BOUNDARY_W)) / (PITCH_H + (2 * GOAL_AREA_H))),
    )
)

TEAM_SIZE = 3

# Colors
BORDER_COLOR = "#ffffff"
BALL_COLOR = "#3c1414"
GREEN = "#7eaf34"
BLUE = "#191970"
RED = "#C41E3A"


class Point:
    x = y = float("inf")

    def __init__(self, coordinates) -> None:
        if type(coordinates) != list or len(coordinates) != 2:
            exit()
        for coordinate in coordinates:
            if coordinate in [None, nan]:
                exit()

        self.x = coordinates[0]
        self.y = coordinates[1]

    def update(self, x, y) -> None:
        if (x in [None, nan]) or (y in [None, nan]):
            exit()

        self.x = x
        self.y = y

    def get_list(self) -> list:
        return [self.x, self.y]

    def euclidean_distance(self, point):
        if type(point) != Point:
            exit()

        return sqrt(pow((self.x - point.x), 2) + pow(self.y - point.y, 2))

    def print(self) -> None:
        print([self.x, self.y])


class Line:
    A = B = C = float("inf")

    def __init__(self, point_1, point_2) -> None:
        if (type(point_1) != Point) or (type(point_2) != Point):
            exit()

        self.A = point_1.y - point_2.y
        self.B = point_1.x - point_2.x
        self.C = (point_1.x * point_2.y) - (point_2.x * point_1.y)

    def contain(self, point) -> bool:
        if type(point) != Point:
            exit()

        return (
            True if ((self.A * point.x) + (self.B * point.y) + self.C) == 0 else False
        )

    def get_y(self, x):
        return -((self.C + (self.A * x)) / self.B)

    def get_x(self, y):
        return -((self.C + (self.B * y)) / self.A)


def find_min_direct_shoot_distance(player, opp_team, goal_range, goal_line_y):
    min_direct_shoot_distance = WIN_H
    for x in range(goal_range[0], goal_range[1] + 1):
        line = Line(player, Point([x, goal_line_y]))
        direct_shoot_possible = True

        for opp_player in opp_team:
            if line.contain(opp_player):
                direct_shoot_possible = False
                break

        if direct_shoot_possible:
            min_direct_shoot_distance = min(
                min_direct_shoot_distance,
                player.euclidean_distance(Point([x, goal_line_y])),
            )

    return min_direct_shoot_distance


def find_goal(player, opp_team, goal_range, goal_line_y):
    min_direct_shoot_distance = WIN_H
    goal = Point([0, 0])
    for x in range(goal_range[0], goal_range[1] + 1):
        line = Line(player, Point([x, goal_line_y]))
        direct_shoot_possible = True

        for opp_player in opp_team:
            if line.contain(opp_player):
                direct_shoot_possible = False
                break

        if direct_shoot_possible:
            if min_direct_shoot_distance > player.euclidean_distance(Point([x, goal_line_y])):
                min_direct_shoot_distance = player.euclidean_distance(Point([x, goal_line_y]))
                goal = Point([x, goal_line_y])

    return goal


def find_dist_from_kicker(player, kicker, opp_team):
    line = Line(player, kicker)
    direct_shoot_possible = True

    for opp_player in opp_team:
        if line.contain(opp_player):
            direct_shoot_possible = False
            break

    return player.euclidean_distance(kicker) if direct_shoot_possible else WIN_H


def random_point_in_red_play_area() -> Point:
    return Point(
        [
            uniform(
                ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2),
                ((WIN_W + (PITCH_W * EXPANSION_FACTOR)) / 2),
            ),
            uniform(((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2), (WIN_H / 2)),
        ]
    )


def random_point_in_penalty_area() -> Point:
    return Point(
        [
            uniform(
                ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
                + (((PITCH_W - PENALTY_AREA_W) * EXPANSION_FACTOR) / 2),
                ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
                + (((PITCH_W + PENALTY_AREA_W) * EXPANSION_FACTOR) / 2),
            ),
            uniform(
                ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2),
                ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2)
                + (PENALTY_AREA_H * EXPANSION_FACTOR),
            ),
        ]
    )


def __init__team() -> list:
    team = []
    for player in range(0, TEAM_SIZE - 1):
        team.append(random_point_in_red_play_area())
    team.append(random_point_in_penalty_area())
    return team


def draw_soccer_pitch_lines(area) -> None:
    pygame.draw.rect(
        SCREEN,
        BORDER_COLOR,
        area,
        width=BOUNDARY_W,
        border_top_left_radius=BOUNDARY_W,
        border_top_right_radius=BOUNDARY_W,
        border_bottom_left_radius=BOUNDARY_W,
        border_bottom_right_radius=BOUNDARY_W,
    )


def draw_team(team, color) -> None:
    for player in range(0, TEAM_SIZE):
        pygame.draw.circle(
            SCREEN, color, team[player].get_list(), (2 * BOUNDARY_W), width=BOUNDARY_W
        )


center_spot = Point([(WIN_W / 2), (WIN_H / 2)])
ball = Point([(WIN_W / 2), (WIN_H / 2)])
kicker = Point([(WIN_W / 2), (WIN_H / 2)])
blue_team = __init__team()
red_team = __init__team()

goal_range = [
    ceil(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
        + (((PITCH_W - GOAL_AREA_W) * EXPANSION_FACTOR) / 2)
    ),
    floor(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
        + (((PITCH_W + GOAL_AREA_W) * EXPANSION_FACTOR) / 2)
    ),
]

min_direct_shoot_distance = [WIN_H, WIN_H, WIN_H]
dist_from_kicker = [WIN_H, WIN_H, WIN_H]
shoot_assister = None
cost = WIN_H
# Determine whether Blue team players, except from the kicker, can take direct shoot out or not.
# If yes, then determine the shortest distance between them and goal.
for i in range(0, 3):
    min_direct_shoot_distance[i] = min(
        min_direct_shoot_distance[i],
        find_min_direct_shoot_distance(
            blue_team[i],
            red_team,
            goal_range,
            ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2) - (2 * BOUNDARY_W),
        ),
    )
    dist_from_kicker[i] = find_dist_from_kicker(blue_team[i], kicker, red_team)
    if cost > (min_direct_shoot_distance[i] + dist_from_kicker[i]):
        shoot_assister = i
        cost = min_direct_shoot_distance[i] + dist_from_kicker[i]

goal = find_goal(blue_team[shoot_assister], red_team, goal_range, ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2) - (2 * BOUNDARY_W))


# Initialising the game
pygame.init()
SCREEN = pygame.display.set_mode([0, 0])
FONT = pygame.font.Font("freesansbold.ttf", 12)


def draw_static():
    cost_meter = FONT.render("Cost: " + str(cost), True, BORDER_COLOR, GREEN)
    cost_meter_rect = cost_meter.get_rect()
    cost_meter_rect.update(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        ((WIN_H + (PITCH_H * EXPANSION_FACTOR)) / 2) + BOUNDARY_W,
        cost_meter_rect.width,
        cost_meter_rect.height,
    )

    SCREEN.fill(GREEN)
    SCREEN.blit(cost_meter, cost_meter_rect)

    pitch = pygame.Rect(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        (PITCH_W * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
        (PITCH_H * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
    )
    red_play_area = pygame.Rect(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        (PITCH_W * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
        ((PITCH_H / 2) * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
    )
    penalty_area = pygame.Rect(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
        - BOUNDARY_W
        + (((PITCH_W - PENALTY_AREA_W) * EXPANSION_FACTOR) / 2),
        ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2) - BOUNDARY_W,
        (PENALTY_AREA_W * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
        (PENALTY_AREA_H * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
    )
    goal_area = pygame.Rect(
        ((WIN_W - (PITCH_W * EXPANSION_FACTOR)) / 2)
        - BOUNDARY_W
        + (((PITCH_W - GOAL_AREA_W) * EXPANSION_FACTOR) / 2),
        ((WIN_H - (PITCH_H * EXPANSION_FACTOR)) / 2)
        - (2 * BOUNDARY_W)
        - (GOAL_AREA_H * EXPANSION_FACTOR),
        (GOAL_AREA_W * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
        (GOAL_AREA_H * EXPANSION_FACTOR) + (2 * BOUNDARY_W),
    )

    draw_soccer_pitch_lines(pitch)
    draw_soccer_pitch_lines(red_play_area)
    draw_soccer_pitch_lines(penalty_area)
    draw_soccer_pitch_lines(goal_area)
    pygame.draw.circle(
        SCREEN,
        BORDER_COLOR,
        center_spot.get_list(),
        (CENTER_SPOT_R * EXPANSION_FACTOR),
        width=BOUNDARY_W,
    )
    pygame.draw.circle(
        SCREEN, BALL_COLOR, ball.get_list(), BOUNDARY_W, width=BOUNDARY_W
    )
    pygame.draw.circle(
        SCREEN, BLUE, kicker.get_list(), 2 * BOUNDARY_W, width=BOUNDARY_W
    )

    draw_team(blue_team, BLUE)
    draw_team(red_team, RED)


draw_static()
pygame.display.flip()

possible_states = [
    "BALL_WITH_KICKER",
    "BALL_GOING_TO_ASSISTER",
    "BALL_WITH_ASSISTER",
    "BALL_GOING_TO_GOAL_AREA",
    "BALL_IN_GOAL_AREA",
]
cost = 0
present_state = possible_states[0]
while True:
    for event in pygame.event.get():
        if (event.type == KEYDOWN and event.key == K_ESCAPE) or (event.type == QUIT):
            exit()
    
    print(ball.get_list())

    pygame.display.flip()
    pygame.time.wait(50)

    if present_state == possible_states[0]:
        present_state = possible_states[1]
    elif present_state == possible_states[1]:
        if ball.x < blue_team[shoot_assister].x:
            if ball.x + 0.5 > blue_team[shoot_assister].x:
                ball.x = blue_team[shoot_assister].x
                ball.y = blue_team[shoot_assister].y
                present_state = possible_states[2]
            else:
                ball.x = ball.x + 0.5
                if ball.y != blue_team[shoot_assister].y:
                    ball.y = (((kicker.y - blue_team[shoot_assister].y) / (kicker.x - blue_team[shoot_assister].x)) * (ball.x - kicker.x)) + kicker.y
        elif ball.x > blue_team[shoot_assister].x:
            if ball.x - 0.5 < blue_team[shoot_assister].x:
                ball.x = blue_team[shoot_assister].x
                ball.y = blue_team[shoot_assister].y
                present_state = possible_states[2]
            else:
                ball.x = ball.x - 0.5
                if ball.y != blue_team[shoot_assister].y:
                    ball.y = (((kicker.y - blue_team[shoot_assister].y) / (kicker.x - blue_team[shoot_assister].x)) * (ball.x - kicker.x)) + kicker.y
        else:
            if ball.y < blue_team[shoot_assister].y:
                if ball.y + 0.5 > blue_team[shoot_assister].y:
                    ball.y = blue_team[shoot_assister].y
                    present_state = possible_states[2]
                else:
                    ball.y = ball.y + 0.5
            else:
                present_state = possible_states[2]
        cost = ball.euclidean_distance(kicker)
    elif present_state == possible_states[2]:
        present_state = possible_states[3]
    elif present_state == possible_states[3]:
        if ball.x < goal.x:
            if ball.x + 0.5 > goal.x:
                ball.x = goal.x
                ball.y = goal.y
                present_state = possible_states[4]
            else:
                ball.x = ball.x + 0.5
                if ball.y != goal.y:
                    ball.y = (((blue_team[shoot_assister].y - goal.y) / (blue_team[shoot_assister].x - goal.x)) * (ball.x - goal.x)) + goal.y
        elif ball.x > goal.x:
            if ball.x - 0.5 < goal.x:
                ball.x = goal.x
                ball.y = goal.y
                present_state = possible_states[4]
            else:
                ball.x = ball.x - 0.5
                if ball.y != goal.y:
                    ball.y = (((blue_team[shoot_assister].y - goal.y) / (blue_team[shoot_assister].x - goal.x)) * (ball.x - goal.x)) + goal.y
        else:
            if ball.y < goal.y:
                if ball.y + 0.5 > goal.y:
                    ball.y = goal.y
                    present_state = possible_states[4]
                else:
                    ball.y = ball.y + 0.5
            else:
                present_state = possible_states[4]
        cost = blue_team[shoot_assister].euclidean_distance(kicker) + ball.euclidean_distance(blue_team[shoot_assister])
    draw_static()
