from collections import deque
import math
import random
import heapq

class Cells:
    EMPTY = 0
    WALL = 1
    DOOR = 2
    ENEMY = 3
    TREASURE = 4
    START = 5
    END = 6

CELL_REPRESENTATION = ['.', '#', '-', 'E', 'T', 'S', 'F']

LEVEL_SIZE = 50

def get_neighbours(cell):
    DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1)]
    retval = []
    for direction in DIRECTIONS:
        next_cell = (cell[0] + direction[0], cell[1] + direction[1])

        if next_cell[0] < 0 or next_cell[0] >= LEVEL_SIZE:
            continue
        if next_cell[1] < 0 or next_cell[1] >= LEVEL_SIZE:
            continue
            
        retval.append(next_cell)
    return retval

# def is_in_room(x,y, level):
#     for dir in DIRECTIONS:
#         next_cell = (x, y)
#         while level[next_cell[0]][next_cell[1]] != CELL_WALL:
#             next_cell = (next_cell[0]+dir[0], next_cell[1] + dir[1])
#             if next_cell[0] < 0 or next_cell[0] >= LEVEL_SIZE:
#                 return False
#             if next_cell[1] < 0 or next_cell[1] >= LEVEL_SIZE:
#                 return False
#     return True

def astar(level, start, destination):

    # Since the player can only move in 4 directions, the Manhattan distance is enough
    # instead of the Euclidian cheaper.
    def heuristic(start, destination):
        return abs(start[0] - destination[0]) + abs(start[1] - destination[1])

    # Holds the cells where we came from.
    previous_cells = {}

    # Holds cells we have already visited
    visited = set()

    # Holds cells we need to visit (f(node) - estimated distance, g(node) - distance so far, prev_node - position we came from, node - current position)
    queue = []
    heapq.heappush(queue, (0, 0, start, start))

    while queue:
        estimated_distance, distance_travelled, previous_cell, cell = heapq.heappop(queue)

        previous_cells[cell] = previous_cell

        if cell in visited:
            continue

        if cell == destination:
            break

        visited.add(cell)

        neighbours = get_neighbours(cell)
        for next_cell in neighbours:
            if next_cell in visited:
                continue
            
            if level[next_cell[1]][next_cell[0]] in [Cells.WALL, Cells.TREASURE, Cells.DOOR]:
                continue
                
            heapq.heappush(queue, (heuristic(next_cell, destination) + distance_travelled + 1, distance_travelled + 1, cell, next_cell))

    if destination not in previous_cells:
        return []

    # Construct path from start to destination

    path = []
    curr_pos = destination
    while curr_pos != start:
        path.append(curr_pos)
        curr_pos = previous_cells[curr_pos]
    
    return path

def evaluate(level):
    
    # We don't want to create too many walls as this will make some areas inaccesible and it also looks ugly
    IDEAL_WALL_COUNT = 600
    # How many treasures do we want per level (on average)
    IDEAL_TREASURE_COUNT = 5
    # How many enemies do we want per level (on average)
    IDEAL_ENEMY_COUNT = 10

    start_pos = None
    end_pos = None
    enemies = []
    treasures = []
    wall_count = 0

    # Go through each cell in the level and count how many instances of each cell type do we have
    for y in range(len(level)):
        for x in range(len(level[y])):
            
            if level[y][x] == Cells.ENEMY:
                    enemies.append((x,y))
            elif level[y][x] == Cells.TREASURE:
                    treasures.append((x,y))
            elif level[y][x] == Cells.START:
                    start_pos = (x,y)
            elif level[y][x] == Cells.END:
                    end_pos = (x,y)
            elif level[y][x] == Cells.WALL:
                    wall_count += 1
    
    # Find the path to the exit
    path_to_victory = astar(level, start_pos, end_pos)

    # Calculate our hieuristic
    return len(path_to_victory) - \
            abs(IDEAL_WALL_COUNT - wall_count) - \
            abs((IDEAL_ENEMY_COUNT - len(enemies)) ** 2) - \
            abs((IDEAL_TREASURE_COUNT - len(treasures)) ** 2)

def mutate_level(level):
    new_level = [ [0] * LEVEL_SIZE for _ in range(LEVEL_SIZE)]

    PROBABILITY = {
        "empty_to_wall_no_neighbour": 0.001,
        "empty_to_wall_with_neighbour": 0.1,
        "empty_to_treasure": 0.0005,
        "empty_to_enemy": 0.0005,
        "wall_to_empty": 0.0005,
        "enemy_to_empty": 0.0005,
        "treasure_to_empty": 0.0005
    }
    
    for y in range(len(level)):
        for x in range(len(level[y])):
            cell = level[y][x]

            new_level[y][x] = cell
            
            if cell == Cells.EMPTY:
                wall_neighbour_count = 0

                for neighbour in get_neighbours((x,y)):
                    if level[neighbour[1]][neighbour[0]] == Cells.WALL:
                        wall_neighbour_count += 1

                if wall_neighbour_count == 0:
                    if random.random() < PROBABILITY["empty_to_wall_no_neighbour"]:
                        new_level[y][x] = Cells.WALL
                else:
                    if random.random() < PROBABILITY["empty_to_wall_with_neighbour"]:
                        new_level[y][x] = Cells.WALL
                
                # If the empty space has not turned into a wall,
                # try turning it into treasure or an enemy
                if new_level[y][x] == Cells.EMPTY:
                    if random.random() < PROBABILITY["empty_to_treasure"]:
                        new_level[y][x] = Cells.TREASURE
                    
                    elif random.random() < PROBABILITY["empty_to_enemy"]:
                        new_level[y][x] = Cells.ENEMY

            
            if cell == Cells.WALL:
                if random.random() < PROBABILITY["wall_to_empty"]:
                    new_level[y][x] = Cells.EMPTY
            
            if cell == Cells.ENEMY:
                if random.random() < PROBABILITY["enemy_to_empty"]:
                    new_level[y][x] = Cells.EMPTY
            
            if cell == Cells.TREASURE:
                if random.random() < PROBABILITY["treasure_to_empty"]:
                    new_level[y][x] = Cells.EMPTY

    return new_level

def print_level(level):
    a = 1
    for row in level:
        for cell in row:
            print(CELL_REPRESENTATION[cell], end="")
        print()
    print('=' * LEVEL_SIZE)

def main():

    ITERATIONS = 30
    MUTATIONS = 20
    CONSIDERED_LEVELS = 3

    level = [ [0] * LEVEL_SIZE for _ in range(LEVEL_SIZE)]
    level[2][2] = Cells.START
    level[LEVEL_SIZE - 2][LEVEL_SIZE - 2] = Cells.END

    curr_levels = [level]
    print_level(level)
    for _ in range(ITERATIONS):
        score = []
        for level in curr_levels:
            possibilities = [mutate_level(level) for _ in range(MUTATIONS)]
            score += [(evaluate(possibility), possibility) for possibility in possibilities]
        score += [(evaluate(level), level) for level in curr_levels]
        random.shuffle(score)
        score.sort(reverse=True)
        print([score_pair[0] for score_pair in score])
        curr_levels = [score_pair[1] for score_pair in score[:CONSIDERED_LEVELS]]

        print_level(curr_levels[0])



if __name__ == "__main__":
    main()
