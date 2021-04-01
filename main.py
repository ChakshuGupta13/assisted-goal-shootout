from math import ceil, floor, nan, sqrt
from ctypes import windll
from random import uniform, seed
from sys import exit
from time import time_ns
from pprint import PrettyPrinter
from pygame.constants import KEYDOWN, K_ESCAPE, QUIT

import pygame

# [TODO] Handle exceptions more properly

# Seeding the random number generater with the current time in nano-seconds
seed(time_ns())

# ----------------
# GLOBAL VARIABLES
# ----------------

# Extracting size (width, height) of the current window / screen
WIN_W, WIN_H = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

# Soccer field dimensions in meters
FIELD_W = 68
FIELD_H = 105
PENALTY_AREA_W = 40.3
PENALTY_AREA_H = 16.5
GOAL_AREA_W = 18.32
GOAL_AREA_H = 5.5
CENTER_SPOT_R = 9.15
# [TODO] After removing the dependencies of player circles on @LINE_W, change LINE_W = 0.12
LINE_W = 5


def from_L(area):
    assert area not in [None, nan]

    return area - LINE_W


def L_till_R(area):
    assert area not in [None, nan]

    return LINE_W + area + LINE_W


def till_R(area):
    assert area not in [None, nan]

    return area + LINE_W


"""
As the window size is expressed in pixels, and exact value mapping of 
the above-mentioned soccer field dimensions (given in meters) to pixels would be inappropriate for display, hence, 
we will map by multiplying them with @SCALE_UP factor to fit soccer field in the window.
"""
SCALE_UP = int(
    min(
        ((WIN_W - (2 * LINE_W)) / FIELD_W),
        ((WIN_H - (4 * LINE_W)) / (FIELD_H + (2 * GOAL_AREA_H))),
    )
)


def x_range_of(area) -> list:
    assert area not in [None, nan]

    return [(WIN_W - (area * SCALE_UP)) / 2, (WIN_W + (area * SCALE_UP)) / 2]


def y_range_of(area) -> list:
    assert area not in [None, nan]

    return [(WIN_H - (area * SCALE_UP)) / 2, (WIN_H + (area * SCALE_UP)) / 2]


UPPER_HALF_X = FIELD_X = x_range_of(FIELD_W)
FIELD_Y = y_range_of(FIELD_H)
UPPER_HALF_Y = [FIELD_Y[0], WIN_H / 2]
PENALTY_AREA_X = x_range_of(PENALTY_AREA_W)
PENALTY_AREA_Y = [UPPER_HALF_Y[0], UPPER_HALF_Y[0] + (PENALTY_AREA_H * SCALE_UP)]
GOAL_AREA_X = x_range_of(GOAL_AREA_W)
GOAL_AREA_Y = [from_L(FIELD_Y[0]) - (GOAL_AREA_H * SCALE_UP), from_L(FIELD_Y[0])]
TEAM_SIZE = 3
# [TODO] @BALL_INCREMENT should not be same for each game.
"""
[Reason] 
Currently, it is increasing one of the coordinates of the ball by 0.5,
but, if the slope of connecting line either between two blue team players or 
between a blue team player and goal line is close to 90 degrees or -270 degrees then 
this value of increment will move the ball very fast per @FRAME_TIME.
"""
BALL_INCREMENT = 0.5
# In micro-seconds
FRAME_TIME = 50

# Hex codes of all the colors used in the game
WHITE = "#FFFFFF"
BROWN = "#3C1414"
GREEN = "#7EAF34"
BLUE = "#191970"
RED = "#C41E3A"


class Point:
    x = y = 0

    def __init__(self, coordinates=[0, 0]) -> None:
        assert (type(coordinates) == list) and (len(coordinates) == 2)
        for coordinate in coordinates:
            assert coordinate not in [None, nan]

        self.x = coordinates[0]
        self.y = coordinates[1]

    def update(self, x, y) -> None:
        assert (x not in [None, nan]) and (y in [None, nan])

        self.x = x
        self.y = y

    def get_list(self) -> list:
        return [self.x, self.y]

    def euclidean_distance(self, point):
        assert type(point) == Point

        return sqrt(pow((self.x - point.x), 2) + pow(self.y - point.y, 2))

    def print(self) -> None:
        PrettyPrinter.pprint(self.get_list())


class Line:
    A = B = C = float("inf")

    def __init__(self, P_1, P_2) -> None:
        assert (type(P_1) == Point) and (type(P_2) == Point)

        self.A = P_1.y - P_2.y
        self.B = P_1.x - P_2.x
        self.C = (P_1.x * P_2.y) - (P_2.x * P_1.y)

    def contain(self, P) -> bool:
        assert type(P) == Point

        return True if ((self.A * P.x) + (self.B * P.y) + self.C) == 0 else False


def find_min_direct_shoot_distance(player, opp_team, goal_range, goal_line_y):
    min_direct_shoot_distance = WIN_H
    for x in range(ceil(goal_range[0]), floor(goal_range[1]) + 1):
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
    for x in range(ceil(goal_range[0]), floor(goal_range[1]) + 1):
        line = Line(player, Point([x, goal_line_y]))
        direct_shoot_possible = True

        for opp_player in opp_team:
            if line.contain(opp_player):
                direct_shoot_possible = False
                break

        if direct_shoot_possible:
            if min_direct_shoot_distance > player.euclidean_distance(
                Point([x, goal_line_y])
            ):
                min_direct_shoot_distance = player.euclidean_distance(
                    Point([x, goal_line_y])
                )
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


def random_upper_half_point() -> Point:
    return Point(
        [
            uniform(UPPER_HALF_X[0], UPPER_HALF_X[1]),
            uniform(UPPER_HALF_Y[0], UPPER_HALF_Y[1]),
        ]
    )


def random_penalty_area_point() -> Point:
    return Point(
        [
            uniform(PENALTY_AREA_X[0], PENALTY_AREA_X[1]),
            uniform(PENALTY_AREA_Y[0], PENALTY_AREA_Y[1]),
        ]
    )


def __init__team() -> list:
    team = []
    for _ in range(0, TEAM_SIZE - 1):
        team.append(random_upper_half_point())
    team.append(random_penalty_area_point())
    return team


kicker = center_spot = Point([(WIN_W / 2), (WIN_H / 2)])
ball = Point([(WIN_W / 2), (WIN_H / 2)])
blue_team = __init__team()
red_team = __init__team()

min_direct_shoot_distance = [WIN_H, WIN_H, WIN_H]
dist_from_kicker = [WIN_H, WIN_H, WIN_H]
assister = None
cost = WIN_H
# Determine whether Blue team players, except from the kicker, can take direct shoot out or not.
# If yes, then determine the shortest distance between them and goal.
for i in range(0, 3):
    min_direct_shoot_distance[i] = min(
        min_direct_shoot_distance[i],
        find_min_direct_shoot_distance(
            blue_team[i], red_team, GOAL_AREA_X, from_L(FIELD_Y[0])
        ),
    )
    dist_from_kicker[i] = find_dist_from_kicker(blue_team[i], kicker, red_team)
    if cost > (min_direct_shoot_distance[i] + dist_from_kicker[i]):
        assister = i
        cost = min_direct_shoot_distance[i] + dist_from_kicker[i]

goal = find_goal(blue_team[assister], red_team, GOAL_AREA_X, from_L(FIELD_Y[0]))


# Initialising the game
pygame.init()

# GLOBAL game variables
SCREEN = pygame.display.set_mode([0, 0])
FONT = pygame.font.Font("freesansbold.ttf", 12)

field = pygame.Rect(
    from_L(FIELD_X[0]),
    from_L(FIELD_Y[0]),
    L_till_R(FIELD_W * SCALE_UP),
    L_till_R(FIELD_H * SCALE_UP),
)
upper_half = pygame.Rect(
    from_L(UPPER_HALF_X[0]),
    from_L(UPPER_HALF_Y[0]),
    L_till_R(FIELD_W * SCALE_UP),
    L_till_R((FIELD_H / 2) * SCALE_UP),
)
penalty_area = pygame.Rect(
    from_L(PENALTY_AREA_X[0]),
    from_L(PENALTY_AREA_Y[0]),
    L_till_R(PENALTY_AREA_W * SCALE_UP),
    L_till_R(PENALTY_AREA_H * SCALE_UP),
)
goal_area = pygame.Rect(
    from_L(GOAL_AREA_X[0]),
    from_L(GOAL_AREA_Y[0]),
    L_till_R(GOAL_AREA_W * SCALE_UP),
    L_till_R(GOAL_AREA_H * SCALE_UP),
)


def draw_lines_of_rect(area) -> None:
    pygame.draw.rect(
        SCREEN, WHITE, area, LINE_W, LINE_W, LINE_W, LINE_W, LINE_W,
    )


def draw_lines_of_circle(area, color, radius) -> None:
    pygame.draw.circle(
        SCREEN, color, area.get_list(), radius, width=LINE_W,
    )


def draw_team(team, team_color) -> None:
    for player in range(0, TEAM_SIZE):
        draw_lines_of_circle(team[player], team_color, (2 * LINE_W))


def set_text_out(text):
    text_out = FONT.render(str(text), True, WHITE, GREEN)
    text_out_rect = text_out.get_rect()
    text_out_rect.update(
        from_L(FIELD_X[0]),
        till_R(FIELD_Y[1]),
        text_out_rect.width,
        text_out_rect.height,
    )
    return text_out, text_out_rect


def draw(cost):
    SCREEN.fill(GREEN)
    draw_lines_of_rect(field)
    draw_lines_of_rect(upper_half)
    draw_lines_of_rect(penalty_area)
    draw_lines_of_rect(goal_area)
    draw_lines_of_circle(center_spot, WHITE, (CENTER_SPOT_R * SCALE_UP))
    draw_lines_of_circle(ball, BROWN, LINE_W)
    draw_lines_of_circle(kicker, BLUE, (2 * LINE_W))
    draw_team(blue_team, BLUE)
    draw_team(red_team, RED)
    text_out, text_out_rect = set_text_out(cost)
    SCREEN.blit(text_out, text_out_rect)


possible_states = [
    "BALL_WITH_KICKER",
    "BALL_GOING_TO_ASSISTER",
    "BALL_WITH_ASSISTER",
    "BALL_GOING_TO_GOAL_AREA",
    "BALL_IN_GOAL_AREA",
]


def get_y(x, P_1, P_2):
    assert (
        type(P_1) == Point
        and type(P_2) == Point
        and x not in [None, nan]
        and P_1.x != P_2.x
    )

    return (((P_1.y - P_2.y) / (P_1.x - P_2.x)) * (x - P_1.x)) + P_1.y


def increment_ball(start, end, state, cost):
    if ball.x < end.x:
        if ball.x + BALL_INCREMENT > end.x:
            ball.x = end.x
            ball.y = end.y
            state = possible_states[2]
        else:
            ball.x = ball.x + BALL_INCREMENT
            if ball.y != end.y:
                ball.y = get_y(ball.x, start, end)
    elif ball.x > end.x:
        if ball.x - BALL_INCREMENT < end.x:
            ball.x = end.x
            ball.y = end.y
            state = possible_states[2]
        else:
            ball.x = ball.x - BALL_INCREMENT
            if ball.y != end.y:
                ball.y = get_y(ball.x, start, end)
    else:
        if ball.y < end.y:
            if ball.y + BALL_INCREMENT > end.y:
                ball.y = end.y
                state = possible_states[2]
            else:
                ball.y = ball.y + BALL_INCREMENT
        else:
            state = possible_states[2]
    cost = ball.euclidean_distance(start)
    return state, cost


def main():
    present_state = possible_states[0]
    cost = 0
    while True:
        for event in pygame.event.get():
            if (event.type == KEYDOWN and event.key == K_ESCAPE) or (
                event.type == QUIT
            ):
                exit()

        draw(cost)
        pygame.display.flip()
        pygame.time.wait(FRAME_TIME)

        if present_state == possible_states[0]:
            present_state = possible_states[1]
        elif present_state == possible_states[1]:
            present_state, cost = increment_ball(
                kicker, blue_team[assister], present_state, cost
            )
        elif present_state == possible_states[2]:
            present_state = possible_states[3]
        elif present_state == possible_states[3]:
            present_state, cost = increment_ball(
                blue_team[assister], goal, present_state, cost
            )


if __name__ == "__main__":
    main()
