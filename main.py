from math import ceil, floor, nan, sqrt
from ctypes import windll
from random import uniform, seed
from sys import exit
from time import time_ns
from pprint import pprint, pformat
from pygame.constants import KEYDOWN, K_ESCAPE, K_RETURN, QUIT

import pygame

# [TODO] Handle exceptions more properly

# Seeding the random number generater with the current time in nano-seconds
seed(time_ns())

# Extracting size (width, height) of the current window / screen
WIN_W, WIN_H = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

# Soccer field dimensions in meters
FIELD_W = 68
FIELD_H = 105
PENALTY_AREA_W = 41
PENALTY_AREA_H = 17
GOAL_AREA_W = 18
GOAL_AREA_H = 6
CENTER_SPOT_R = 9
# [TODO] After removing the dependencies of player circles on @LINE_W, change LINE_W = 1
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
SPEED = LINE_W
# In micro-seconds
FRAME_TIME = 100

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

    def update(self, P) -> None:
        assert type(P) == Point and P.is_valid()

        self.x = P.x
        self.y = P.y

    def is_valid(self) -> bool:
        return self.x not in [None, nan] and self.y not in [None, nan]

    def get_list(self) -> list:
        return [self.x, self.y]

    def distance(self, point):
        assert type(point) == Point

        return sqrt(pow((self.x - point.x), 2) + pow(self.y - point.y, 2))

    def print(self) -> None:
        pprint(self.get_list())


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


def add_suitable_point(team: list, all_players: list, suitablity_check) -> None:
    P = suitablity_check()
    while P in all_players:
        P = suitablity_check()
    team.append(P)
    all_players.append(P)


def __init__team(all_players: list) -> list:
    team = []
    for _ in range(0, TEAM_SIZE - 1):
        add_suitable_point(team, all_players, random_upper_half_point)
    add_suitable_point(team, all_players, random_upper_half_point)
    return team


kicker = center_spot = Point([WIN_W / 2, WIN_H / 2])
all_players = [kicker]
ball = Point([WIN_W / 2, WIN_H / 2])
blue_team = __init__team(all_players)
red_team = __init__team(all_players)

kicker_r = 3 * LINE_W
ball_r = 2 * LINE_W
blue_team_r = [(3 * LINE_W)] * TEAM_SIZE
red_team_r = [(3 * LINE_W)] * TEAM_SIZE


def intersection(P3: Point, P2: Point, P1: Point) -> Point:
    """
    Consider: 
        S : A straight line through @P1 and @P2.
        P : A straight line perpendicular to S through @P3.
    Return the point of intersection of S and P.
    """
    assert P3.is_valid() and P2.is_valid() and P1.is_valid()

    A = P2.y - P1.y
    B = P2.x - P1.x
    k = ((A * (P3.x - P1.x)) - (B * (P3.y - P1.y))) / (pow(A, 2) + pow(B, 2))

    return Point([P3.x - (k * A), P3.y + (k * B)])


def is_bounded(P3: Point, P1: Point, P2: Point) -> bool:
    """
    If @P4 lies between @P1 and @P2,
    then it will divide the line segment @P1 - @P2 in some ratio 1:q,
    hence, @P4.x should equal to ((@P2.x + (q * @P1.x)) / (1 + q)),
    so, if q is > 0 then our assumption is correct.
    Let: 
        S  : A straight line through @P1 and @P2.
        P1 : A straight line perpendicular to S through @P1.
        P2 : A straight line perpendicular to S through @P2.
    Returns True if @P3 lies in the region bounded by P1 and P2.
    """
    assert P3.is_valid() and P2.is_valid() and P1.is_valid()

    P4 = intersection(P3, P2, P1)

    return (P4.x - P2.x) * (P1.x - P4.x) > 0


def is_reachable(stop: Point, start: Point) -> bool:
    """
    Returns True if the path till @stop from @start is obstacle-free
    i.e. no red team player is in proximity of the path.
    """
    assert stop.is_valid() and start.is_valid()

    for player in range(0, TEAM_SIZE):
        if is_bounded(red_team[player], stop, start):
            if (
                intersection(red_team[player], stop, start).distance(red_team[player])
                < red_team_r[player] + ball_r
            ):
                return False
    return True


def immediate_goal_point_reachable_by(blue_player: Point):
    assert blue_player.is_valid()

    distance_till_final_goal_point = float("inf")
    final_goal_point = Point()

    for goal_point_x in range(ceil(GOAL_AREA_X[0]), floor(GOAL_AREA_X[1]) + 1):
        goal_point = Point([goal_point_x, GOAL_AREA_Y[1]])

        if is_reachable(goal_point, blue_player):
            distance_till_goal_point = blue_player.distance(goal_point)

            if distance_till_final_goal_point > distance_till_goal_point:
                distance_till_final_goal_point = distance_till_goal_point
                final_goal_point.update(goal_point)

    return final_goal_point if distance_till_final_goal_point != float("inf") else None


def create_graph(adj_mat: list, visited: list) -> None:
    for player in range(0, TEAM_SIZE):
        goal_point = immediate_goal_point_reachable_by(blue_team[player])

        if goal_point != None:
            adj_mat.append(
                [[blue_team[player].get_list(), 0], [goal_point.get_list(), 1]]
            )
            visited.append([goal_point.get_list(), False])

        if is_reachable(blue_team[player], kicker):
            adj_mat.append([[kicker.get_list(), 0], [blue_team[player].get_list(), 0]])

        for other_player in range(player + 1, TEAM_SIZE):
            if is_reachable(blue_team[other_player], blue_team[player]):
                adj_mat.append(
                    [
                        [blue_team[player].get_list(), 0],
                        [blue_team[other_player].get_list(), 0],
                    ]
                )
                adj_mat.append(
                    [
                        [blue_team[other_player].get_list(), 0],
                        [blue_team[player].get_list(), 0],
                    ]
                )
        visited.append([blue_team[player].get_list(), False])
    visited.append([kicker.get_list(), False])


def traverse_graph(node: list, path: list, paths: list) -> None:
    for nodes in adj_mat:
        if nodes[0][0] != node:
            continue
        for node_info in visited:
            if node_info[0] != nodes[1][0] or node_info[1] == True:
                continue

            path.append(nodes[1][0])
            if nodes[1][1] == 1:
                paths.append(list(path))
            else:
                node_info[1] = True
                traverse_graph(nodes[1][0], path, paths)
                node_info[1] = False
            path.pop()
            break


def cost_of(path: list):
    for coordinates in path:
        assert type(coordinates) == list and len(coordinates) == 2
        for coordinate in coordinates:
            assert coordinate not in [None, nan]

    path_cost = 0
    for index in range(1, len(path)):
        path_cost += Point(path[index - 1]).distance(Point(path[index]))

    return path_cost


def in_notation(paths: list) -> list:
    paths_in_notation = []

    if paths == []:
        return paths_in_notation

    for path in paths:
        if path == []:
            paths_in_notation.append([])
            continue

        path_in_notation = ["Kicker"]
        for coordinates in range(1, len(path) - 1):
            for index in range(0, TEAM_SIZE):
                if path[coordinates] == blue_team[index].get_list():
                    path_in_notation.append(str(index))
                    break
        path_in_notation.append("Goal")
        paths_in_notation.append(path_in_notation)

    return paths_in_notation


adj_mat = []
visited = []
all_paths = []
create_graph(adj_mat, visited)
traverse_graph(kicker.get_list(), [kicker.get_list()], all_paths)
all_paths.sort(key=cost_of)
all_paths_in_notation = in_notation(all_paths)


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


def draw_player_name(text: str, team_color, player: Point, player_r) -> None:
    text_out = FONT.render(text, True, team_color, GREEN)
    text_out_rect = text_out.get_rect()
    text_out_rect.update(
        player.x,
        player.y + (player_r + LINE_W),
        text_out_rect.width,
        text_out_rect.height,
    )
    SCREEN.blit(text_out, text_out_rect)


def draw_team(team, team_color, radius) -> None:
    for player in range(0, TEAM_SIZE):
        draw_lines_of_circle(team[player], team_color, radius[player])
        draw_player_name(str(player), team_color, team[player], radius[player])


def set_text_out(text: str):
    text_out = FONT.render(text, True, WHITE, GREEN)
    text_out_rect = text_out.get_rect()
    text_out_rect.update(
        from_L(FIELD_X[0]),
        till_R(FIELD_Y[1]),
        text_out_rect.width,
        text_out_rect.height,
    )
    return text_out, text_out_rect


def print_text(text: str, y_offset):
    text_out = FONT.render(text, True, WHITE, GREEN)
    text_out_rect = text_out.get_rect()
    text_out_rect.update(
        from_L(FIELD_X[0]),
        till_R(FIELD_Y[1]) + y_offset,
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
    draw_lines_of_circle(ball, BROWN, ball_r)
    draw_lines_of_circle(kicker, BLUE, kicker_r)
    draw_player_name("Kicker", BLUE, kicker, kicker_r)
    draw_team(blue_team, BLUE, blue_team_r)
    draw_team(red_team, RED, red_team_r)
    text_out, text_out_rect = set_text_out(cost)
    SCREEN.blit(text_out, text_out_rect)
    text_out, text_out_rect = print_text(
        pformat(all_paths_in_notation[0]) + " : " + str(cost_of(all_paths[0])),
        text_out_rect.height,
    )
    SCREEN.blit(text_out, text_out_rect)
    text_out, text_out_rect = print_text(
        pformat(all_paths_in_notation[1]) + " : " + str(cost_of(all_paths[1])),
        2 * text_out_rect.height,
    )
    SCREEN.blit(text_out, text_out_rect)
    text_out, text_out_rect = print_text(
        "Press ESC to Quit.", 3 * text_out_rect.height,
    )
    SCREEN.blit(text_out, text_out_rect)


def get_y(x, P_1, P_2):
    assert (
        type(P_1) == Point
        and type(P_2) == Point
        and x not in [None, nan]
        and P_1.x != P_2.x
    )

    return (((P_1.y - P_2.y) / (P_1.x - P_2.x)) * (x - P_1.x)) + P_1.y


def increment_ball(start: Point, end: Point, moving: bool):
    adjacent = abs(end.x - start.x)
    opposite = abs(end.y - start.y)
    hypotenuse = sqrt(pow(adjacent, 2) + pow(opposite, 2))

    BALL_INCREMENT = (adjacent / hypotenuse) * SPEED

    if ball.x < end.x:
        if ball.x + BALL_INCREMENT > end.x:
            ball.x = end.x
            ball.y = end.y
            moving = False
        else:
            ball.x = ball.x + BALL_INCREMENT
            if ball.y != end.y:
                ball.y = get_y(ball.x, start, end)
    elif ball.x > end.x:
        if ball.x - BALL_INCREMENT < end.x:
            ball.x = end.x
            ball.y = end.y
            moving = False
        else:
            ball.x = ball.x - BALL_INCREMENT
            if ball.y != end.y:
                ball.y = get_y(ball.x, start, end)
    else:
        if ball.y < end.y:
            if ball.y + BALL_INCREMENT > end.y:
                ball.y = end.y
                moving = False
            else:
                ball.y = ball.y + BALL_INCREMENT
        else:
            moving = False
    return moving, ball.distance(start)


def main():
    index = 0
    moving = False
    cost = 0
    total_cost = 0

    while True:
        for event in pygame.event.get():
            if (event.type == KEYDOWN and event.key == K_ESCAPE) or (
                event.type == QUIT
            ):
                return

        draw(
            ("Cost incurred till now: " + str(total_cost + cost))
            if len(all_paths[0])
            else "Goal Shootout not possible."
        )
        pygame.display.flip()
        pygame.time.wait(FRAME_TIME)

        if index >= len(all_paths[0]) - 1:
            while True:
                for event in pygame.event.get():
                    if event.type == KEYDOWN or event.type == QUIT:
                        return

        moving = True
        moving, cost = increment_ball(
            Point(all_paths[0][index]), Point(all_paths[0][index + 1]), moving
        )
        if moving == False:
            index += 1
            total_cost += cost
            cost = 0


if __name__ == "__main__":
    main()
