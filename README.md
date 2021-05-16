# Assisted Goal Shootout

This repository stores the implemenation of a small game, build using [Pygame](https://www.pygame.org/), which was part of the Assignment-1 of the course Artificial Intellegence - II (CSL7040) (Trimester III - AY 2020-21) ([Indian Institute of Technology Jodhpur](https://iitj.ac.in/)).

## Game

- The game played is soccer / football with very simplified rules.
- There are two teams: BLUE and RED.
- The upper half of the game field is the RED team's area.
- There are 4 players in team BLUE and 3 players in team RED.
- One player of the team BLUE, hereafter referred to as "Kicker", is at the center spot and is also our agent.
- All player except Kicker are in the upper half of the game field.
- There must be at least 1 player from each team in the penalty area of the upper half of the game field.
- Aim: Kicker have to perform an assisted goal shootout, with minimum cost, which means that Kicker must pass the ball at least once to some other player of its team then that player might pass the ball to someother player or perform direct goal shootout.
- Cost of the assisted goal shootout is the distance travelled by the ball until the goal.
- The ball passes form a straight line trajectory because the game is played in 2-dimentional space.
- Before each run of the game, except Kicker's position, all the players' position must be randomaly allocated within / on the game field boundary, following the above-mentioned rules.
- Each player is represented by a point on 2-D plane and each player has an area of control within which if the ball comes then that player will be in control of the ball.
- The ball can be passed to another player is the condition showed in the image below is satisfied:
![Obstacle in a ball pass path](https://user-images.githubusercontent.com/35608680/118394222-fa74b400-b660-11eb-9a71-500e42249318.png)
- The transitions of the ball in the game are shown as below:
![Soccer's Game - Transition](https://user-images.githubusercontent.com/35608680/118394284-5b9c8780-b661-11eb-9c4e-d043a1c9ba38.png)

### Start the Game

Run the main.py file. Note that the implementation was build using [Python 3.8](https://docs.python.org/3.8/). 

### End the Game

Press ESC key on the keyboard to quit the game.
