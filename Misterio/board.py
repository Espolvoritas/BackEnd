from itertools import combinations
from collections import defaultdict

def indexed_on_one(cells, neighbors, free_neighbors):
    new_cells = [(x+1, y+1, t) for (x, y, t) in cells]
    new_neighbors = defaultdict(lambda: set())
    new_free_neighbors = defaultdict(lambda: set())

    for x, y, t in neighbors.keys():
        new = {(w+1, z+1, s) for (w, z, s) in neighbors[(x, y, t)]}
        new_neighbors[(x+1, y+1, t)] = new

    for x, y, t in free_neighbors.keys():
        new = {(w+1, z+1, s) for (w, z, s) in free_neighbors[(x, y, t)]}
        new_free_neighbors[(x+1, y+1, t)] = new

    return new_cells, new_neighbors, new_free_neighbors

def make_board():
    neighbors = defaultdict(lambda: set())
    free_neighbors = defaultdict(lambda: set())

    rooms = [(2, 2, "GARAGE"), (2, 10, "LOBBY"),
             (2, 17, "CELLAR"), (11, 15, "HALL"),
             (16, 16, "LAB"), (16, 10, "PANTHEON"),
             (16, 2, "LIBRARY"), (10, 3, "ROOM")]

    entrances = [(0, 6, "entrance"), (0, 13, "entrance"), 
                 (6, 0, "entrance"), (13, 0, "entrance"), 
                 (6, 19, "entrance"), (13, 19, "entrance"),
                 (19, 13, "entrance"), (19, 6, "entrance")]
    
    room_entrances = [(4, 6, "entrance- LOBBY"), (6, 10, "entrance- LOBBY"),
                     (3, 13, "entrance- LOBBY"), (6, 2, "entrance- GARAGE"),
                     (13, 4, "entrance- LIBRARY"), (13, 10, "entrance- PANTHEON"),
                     (16, 13, "entrance- PANTHEON"), (15, 6, "entrance- PANTHEON"),
                     (13, 16, "entrance- LAB"), (10, 6, "entrance- ROOM"),
                     (10, 13, "entrance- HALL"), (6, 15, "entrance- CELLAR")]

    portals = [(6, 4, "vampire"), (13, 3, "scorpion"),
               (6, 14, "vampire"), (13, 14, "scorpion"),
               (14, 6, "cobra"), (4, 13, "tarantula"),
               (3, 6, "cobra"), (15, 13, "tarantula")]

    traps = [(6, 6, "Trap"), (6, 13, "Trap"),
             (13, 6, "Trap"), (13, 13, "Trap")]

    plain = []
    
    all_cells = rooms + entrances + room_entrances + portals + traps

    special_cell_coords = set([(x, y) for x, y, t in all_cells])
    plain_cell_coords = set()

    for i in [6, 13]:
        for j in range(0, 20):
            if (j, i) not in special_cell_coords:
                plain_cell_coords.add((j, i))
            if (i, j) not in special_cell_coords:
                plain_cell_coords.add((i, j))

    for x, y in plain_cell_coords:
        plain.append((x, y, "plain"))

    all_cells = all_cells + plain

    for (c1, c2) in combinations(all_cells, 2):
        x, y, t = c1
        w, z, s = c2
        xdist = abs(x - w)
        ydist = abs(y - z)
        if xdist + ydist == 1: # the distance between c1 and c2 is exactly 1
            neighbors[c1].add(c2)
            neighbors[c2].add(c1)


    for (t, s) in combinations(traps, 2):
        free_neighbors[s].add(t)
        free_neighbors[t].add(s)

    for (p, q) in combinations(portals, 2):
        if p[2] == q[2]:
            free_neighbors[p].add(q)
            free_neighbors[q].add(p)

    for e in room_entrances:
        for r in rooms:
            if r[2] in e[2]:
                free_neighbors[e].add(r)
                free_neighbors[r].add(e)
                
    for (r, s) in combinations(rooms, 2):
        if r[2] == s[2]:
            free_neighbors[r].add(s)
            free_neighbors[s].add(r)

    all_cells, neighbors, free_neighbors = indexed_on_one(all_cells, neighbors, free_neighbors)
    return all_cells, neighbors, free_neighbors