from itertools import combinations
from collections import defaultdict

def indexedOnOne(cells, neighbors, freeNeighbors):
    newCells = [(x+1, y+1, t) for (x, y, t) in cells]
    newNeighbors = defaultdict(lambda: set())
    newFreeNeighbors = defaultdict(lambda: set())

    for x, y, t in neighbors.keys():
        new = {(w+1, z+1, s) for (w, z, s) in neighbors[(x, y, t)]}
        newNeighbors[(x+1, y+1, t)] = new

    for x, y, t in freeNeighbors.keys():
        new = {(w+1, z+1, s) for (w, z, s) in freeNeighbors[(x, y, t)]}
        newFreeNeighbors[(x+1, y+1, t)] = new

    return newCells, newNeighbors, newFreeNeighbors

def makeBoard():
    neighbors = defaultdict(lambda: set())
    freeNeighbors = defaultdict(lambda: set())

    rooms = [(2, 2, "GARAGE"), (2, 10, "LOBBY"),
             (2, 17, "CELLAR"), (11, 15, "HALL"),
             (16, 16, "LAB"), (16, 10, "PANTHEON"),
             (16, 2, "LIBRARY"), (10, 3, "ROOM")]

    entrances = [(0, 6, "entrance"), (0, 13, "entrance"), 
                 (6, 0, "entrance"), (13, 0, "entrance"), 
                 (6, 19, "entrance"), (13, 19, "entrance"),
                 (19, 13, "entrance"), (19, 6, "entrance")]
    
    roomEntrances = [(4, 6, "entrance- LOBBY"), (6, 10, "entrance- LOBBY"),
                     (3, 13, "entrance- LOBBY"), (6, 2, "entrance- GARAGE"),
                     (13, 4, "entrance- LIBRARY"), (13, 10, "entrance- PANTHEON"),
                     (16, 13, "entrance- PANTHEON"), (15, 6, "entrance- PANTHEON"),
                     (13, 16, "entrance- LAB"), (10, 6, "entrance- ROOM"),
                     (10, 13, "entrance- HALL"), (6, 15, "entrance- CELLAR")]

    portals = [(6, 4, "vampire"), (13, 3, "scorpion"),
               (6, 14, "vampire"), (13, 14, "scorpion"),
               (14, 6, "cobra"), (4, 13, "tarantula"),
               (3, 6, "cobra"), (15, 13, "tarantula")]

    traps = [(6, 6, "trap"), (6, 13, "trap"),
             (13, 6, "trap"), (13, 13, "trap")]

    plain = []
    
    allCells = rooms + entrances + roomEntrances + portals + traps

    specialCellCoordinates = set([(x, y) for x, y, t in allCells])
    plainCellCoordinates = set()

    for i in [6, 13]:
        for j in range(0, 20):
            if (j, i) not in specialCellCoordinates:
                plainCellCoordinates.add((j, i))
            if (i, j) not in specialCellCoordinates:
                plainCellCoordinates.add((i, j))

    for x, y in plainCellCoordinates:
        plain.append((x, y, "plain"))

    allCells = allCells + plain

    for (c1, c2) in combinations(allCells, 2):
        x, y, t = c1
        w, z, s = c2
        xdist = abs(x - w)
        ydist = abs(y - z)
        if xdist + ydist == 1: # the distance between c1 and c2 is exactly 1
            neighbors[c1].add(c2)
            neighbors[c2].add(c1)


    for (t, s) in combinations(traps, 2):
        freeNeighbors[s].add(t)
        freeNeighbors[t].add(s)

    for (p, q) in combinations(portals, 2):
        if p[2] == q[2]:
            freeNeighbors[p].add(q)
            freeNeighbors[q].add(p)

    for e in roomEntrances:
        for r in rooms:
            if r[2] in e[2]:
                freeNeighbors[e].add(r)
                freeNeighbors[r].add(e)
                
    for (r, s) in combinations(rooms, 2):
        if r[2] == s[2]:
            freeNeighbors[r].add(s)
            freeNeighbors[s].add(r)

    allCells, neighbors, freeNeighbors = indexedOnOne(allCells, neighbors, freeNeighbors)
    return allCells, neighbors, freeNeighbors