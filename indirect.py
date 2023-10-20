from collections import deque
import math
import random
import heapq

LEVEL_SIZE = 50

# Indirect content representation:
# List of rooms

class Room:
    def __init__(self, x, y, width, height, enemies, treasures):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.enemies = enemies
        self.treasures = treasures

def getEmptyLevel():
    return []

# https://www.jeffreythompson.org/collision-detection/rect-rect.php
def are_rooms_colliding(room1, room2):
    if room1.x <= room2.x + room2.width and \
        room1.x + room1.width >= room2.x and \
        room1.y <= room2.y + room2.height and \
        room1.y + room1.height >= room2.y:

        return True
    return False

def is_point_in_room(point, room):
    if room.x < point[0] and \
        point[0] < room.x + room.width and \
        room.y < point[1] and \
        point[1] < room.y + room.height:

        return True
    
    return False

# TODO: explain this
def density_error_function(ideal, actual):
        return 3*(math.exp(abs(ideal - actual)*10)-1)

def evaluate(level):

    if len(level) == 0:
        return (9999,)

    IDEAL_NO_OF_ROOMS = 9999    # Create as many rooms as you can
    IDEAL_ENEMY_DENSITY = 1/(5*5)       # What fraction of the room should be enemies (2 enemies in a 5x5 room on average)
    IDEAL_TREASURE_DENSITY = 0.5/(5*5)  # What fraction of the room should be covered in treasure chests (one treasure in every second 5x5 room)

    # Rooms that are overlapping will be discarded
    no_of_rooms = len(level)
    enemy_density = 0
    treasure_density = 0

    # TODO: what about one room colliding with multiple
    for room_index, room in enumerate(level):

        for other_room in level[(room_index+1):]:
            if are_rooms_colliding(room, other_room):
                no_of_rooms -= 2
                break
        
        # TODO: this does not take into consideration overlapping rooms
        enemy_density += density_error_function(IDEAL_ENEMY_DENSITY, room.enemies / (room.width * room.height))
        treasure_density += density_error_function(IDEAL_TREASURE_DENSITY, room.treasures / (room.width * room.height))

    room_count_error = abs(IDEAL_NO_OF_ROOMS - max(no_of_rooms, 0)*4)

    return (room_count_error, enemy_density / len(level), treasure_density / len(level))


def mutate_level(level):
    new_level = []
    for room in level:
        # Random chance to delete this level
        if random.random() < 0.05:
            continue

        room.x = min(max(0, room.x + random.randint(-1,1)), LEVEL_SIZE)
        room.y = min(max(0, room.y + random.randint(-1,1)), LEVEL_SIZE)
        room.width = max(min(room.width + random.randint(-1,1), LEVEL_SIZE - room.x), 5)
        room.height = max(min(room.height + random.randint(-1,1), LEVEL_SIZE - room.y), 5)

        enemies_copy = room.enemies
        treasures_copy = room.treasures

        room.enemies = max(0, room.enemies + random.randint(-2, 2))
        room.treasures = max(0, room.treasures + random.randint(-2, 2))

        # Do not add new enemies or treasures if it fills up the room
        if (room.enemies + room.treasures) >= ( (room.width-2) * (room.height-2) / 2):
            room.enemies = enemies_copy
            room.treasures = treasures_copy

        new_level.append(room)
    
    # Random chance to add new levels
    if random.random() < 0.1:
        width = random.randint(4,10)
        height = random.randint(4,10)
        enemies = random.randint(0, max(5,  int((width-2) * (height-2) / 4)))
        treasures = random.randint(0, max(1, int((width-2) * (height-2) / 4)))
        new_level.append(Room(
            random.randint(0,40),     # x
            random.randint(0,40),     # y
            width,                    # width
            height,                   # height
            enemies,                  # enemies
            treasures                 # treasures
        ))
    
    return new_level

def print_level(level):
    for room in level:
        print(room.x, room.y, room.width, room.height, room.enemies, room.treasures)
    
    enemies = []
    treasures = []

    for room in level:
        for _ in range(room.enemies):
            tries= 1
            enemy = (
                random.randint(room.x + 1, room.x + room.width - 2),
                random.randint(room.y + 1, room.y + room.height - 2)
            )

            while (enemy in treasures + enemies) and (tries < 10):
                enemy = (
                    random.randint(room.x + 1, room.x + room.width - 2),
                    random.randint(room.y + 1, room.y + room.height - 2)
                )
                tries += 1

            enemies.append(enemy)

        for _ in range(room.treasures):
            tries = 1
            treasure = (
                random.randint(room.x + 1, room.x + room.width - 2),
                random.randint(room.y + 1, room.y + room.height - 2)
            )

            while (treasure in treasures + enemies) and (tries < 10):
                treasure = (
                    random.randint(room.x + 1, room.x + room.width - 2),
                    random.randint(room.y + 1, room.y + room.height - 2)
                )
                tries += 1

            treasures.append(treasure)
    
    for y in range(LEVEL_SIZE):
        for x in range(LEVEL_SIZE):
            if (x,y) in enemies:
                print("E", end="")
                continue
            
            if (x,y) in treasures:
                print("T", end="")
                continue
            
            is_wall = False
            for room1 in level:
                if (x == room1.x and y >= room1.y and y <= room1.y + room1.height) or \
                    (x == room1.x + room1.width and y >= room1.y and y <= room1.y + room1.height) or \
                    (y == room1.y and x >= room1.x and x <= room1.x + room1.width) or \
                    (y == room1.y + room1.height and x >= room1.x and x <= room1.x + room1.width):


                    is_wall = True
                    for room2 in level:
                        if is_point_in_room((x,y), room1):
                            is_wall = False
                            break

                    if not is_wall:
                        break

            if is_wall:
                print("#", end="")
                continue
            
            print(".", end="")
        print()
    
    print('=' * LEVEL_SIZE)


def main():

    # Constants for exploration
    ITERATIONS = 600           # No. of iterations the algorithm will run for
    MUTATIONS_PER_LEVEL = 6  # How many new levels to generate for each existing level
    CONSIDERED_LEVELS = 10     # How many levels to keep at the end of an iteration
    
    # Create an array to store our levels and add the initial level
    curr_levels = [getEmptyLevel()]
    print_level(curr_levels[0])
    
    # The core of the algorithm
    for _ in range(ITERATIONS):
        score = []
        
        # Create new levels by from mutating existing ones
        for level in curr_levels:
            possibilities = [mutate_level(level) for _ in range(MUTATIONS_PER_LEVEL)]
            # Keep the level along with its score
            score += [(evaluate(possibility), possibility) for possibility in possibilities]
        # Add the levels from the previous iteration
        score += [(evaluate(level), level) for level in curr_levels]
        # Shuffle the levels 
        random.shuffle(score)
        # Sort the levels by score, from highest to lowest
        score.sort(reverse=True, key=lambda x: 9999-sum(x[0]))
        print([(score_pair[0], 9999-sum(score_pair[0])) for score_pair in score])
        print([len(score_pair[1]) for score_pair in score])
        # Discard weak levels
        curr_levels = [score_pair[1] for score_pair in score[:CONSIDERED_LEVELS]]

        print_level(curr_levels[0])

if __name__ == "__main__":
    main()