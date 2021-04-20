import math
from itertools import chain, groupby

from Model import Direction


def get_tsp(src_pos, dest_pos, graph):
    graph.find_all_shortest_path()

    bread_tsp = make_tsp(graph.nodes[src_pos], graph.nodes[dest_pos], 'bread', graph)
    grass_tsp = make_tsp(graph.nodes[src_pos], graph.nodes[dest_pos], 'grass', graph)

    return {
        'tsp_bread': bread_tsp,
        'tsp_grass': grass_tsp,
    }


def make_dist_graph(src, dest, name_of_node_object, graph, dist_nodes):
    number_of_dist_vertex = len(dist_nodes) + 2

    dist = [number_of_dist_vertex * [-math.inf] for _ in range(number_of_dist_vertex)]

    dist_src = 0
    dist_dest = number_of_dist_vertex - 1

    dist[dist_src][dist_dest] = getattr(src, f'{name_of_node_object}_value')(src, dest, graph)
    for i in range(number_of_dist_vertex - 2):
        node1 = dist_nodes[i]
        dist[dist_src][i + 1] = getattr(node1, f'{name_of_node_object}_value')(src, dest, graph)
        dist[i + 1][dist_dest] = getattr(dest, f'{name_of_node_object}_value')(node1, dest, graph)
        for j in range(number_of_dist_vertex - 2):
            node2 = dist_nodes[j]
            dist[i + 1][j + 1] = getattr(node2, f'{name_of_node_object}_value')(node1, dest, graph)

    return dist


def make_tsp(src, dest, name_of_node_object, graph):
    dist_nodes = getattr(graph, f'get_nearest_{name_of_node_object}_nodes')(src, dest)

    dist = make_dist_graph(src, dest, name_of_node_object, graph, dist_nodes)

    number_of_dist_vertex = len(dist_nodes) + 2

    dp = [number_of_dist_vertex * [-math.inf] for _ in range(1 << number_of_dist_vertex)]
    dp_path = [number_of_dist_vertex * [-1] for _ in range(1 << number_of_dist_vertex)]

    dist_src = 0

    for i in range(1 << number_of_dist_vertex):
        vertices = []
        for j in range(number_of_dist_vertex):
            if i & (1 << j):
                vertices.append(j)
        if len(vertices) == 1 and dist_src not in vertices:
            continue
        elif len(vertices) == 1:
            dp[i][dist_src] = 0
            dp_path[i][dist_src] = dist_src
        for j in vertices:
            for k in vertices:
                if j == k:
                    continue
                value = dp[i - (1 << j)][k] + dist[k][j]
                if dp[i][j] < value:
                    dp[i][j] = value
                    dp_path[i][j] = k

    return {
        'dp': dp,
        'dp_path': dp_path,
        'dist_nodes': list(chain([src], dist_nodes, [dest])),
    }


def get_tsp_path(src_pos, dest_pos, graph, limit):
    tsp_info = get_tsp(src_pos, dest_pos, graph)

    bread_path_from_tsp_info = get_path_from_tsp_info(tsp_info, 'bread', graph, limit)
    grass_path_from_tsp_info = get_path_from_tsp_info(tsp_info, 'grass', graph, limit)

    return {
        'bread_path_from_tsp_info': bread_path_from_tsp_info,
        'grass_path_from_tsp_info': grass_path_from_tsp_info,
    }


def get_path_from_tsp_info(tsp_info, name_of_node_object, graph, limit):
    dp = tsp_info.get(f'tsp_{name_of_node_object}').get('dp')
    dp_path = tsp_info.get(f'tsp_{name_of_node_object}').get('dp_path')
    dist_nodes = tsp_info.get(f'tsp_{name_of_node_object}').get('dist_nodes')
    number_of_dist_vertex = len(dist_nodes)
    best_mask = None
    best_value = 0
    for i in range(1 << (number_of_dist_vertex - 2)):
        mask = (i << 1) | 1 | (1 << (number_of_dist_vertex - 1))
        number_of_obj = 0
        value = dp[mask][number_of_dist_vertex - 1]
        if best_mask and value < best_value:
            continue
        for j in range(number_of_dist_vertex):
            if mask & (1 << j):
                number_of_obj += getattr(dist_nodes[j], name_of_node_object, 0)
        if number_of_obj >= limit.get(name_of_node_object).get('min'):
            best_mask = mask
            best_value = value

    if not best_mask:
        return None

    path = []
    mask = best_mask
    last = number_of_dist_vertex - 1
    while dp_path[mask][last] != last:
        path.append(last)
        new_mask = mask - (1 << last)
        last = dp_path[mask][last]
        mask = new_mask
    path.append(last)
    path = list(reversed(path))
    actual_path = []

    for i in range(1, len(path)):
        actual_path.extend(
            graph.get_shortest_path_from_shortest_path_info(dist_nodes[path[i - 1]], dist_nodes[path[i]]))

    return {
        'path': [el[0] for el in groupby(actual_path)],
        'value': dp[best_mask][number_of_dist_vertex - 1],
    }


def get_tsp_first_move(src_pos, dest_pos, graph, name_of_object, limit=None):
    if not limit:
        limit = {
            'bread': {
                'min': 1,
            },
            'grass': {
                'min': 1,
            }
        }
    if not limit.get('bread'):
        limit['bread'] = {'min': 1}
    if not limit.get('grass'):
        limit['grass'] = {'min': 1}
    # print('graphhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh')
    # print(graph.nodes)
    # print(src_pos, dest_pos)
    # print('graphhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh')

    all_tsp = get_tsp_path(src_pos, dest_pos, graph, limit)
    tsp_path = all_tsp.get(f'{name_of_object}_path_from_tsp_info') or all_tsp.get(
        f'{"bread" if name_of_object == "grass" else "grass"}_path_from_tsp_info'
    )
    if not tsp_path or not tsp_path.get('path'):
        return Direction.get_value('None')
    p = []
    last = src_pos
    print([i.pos for i in tsp_path.get('path')])
    for i in tsp_path.get('path'):
        p.append(graph.step(last, i.pos))
        last = i.pos
    print(p)
    return Direction.get_value(graph.step(src_pos, tsp_path.get('path')[0].pos))


def get_limit(name_of_object, **kwargs):
    return {
        name_of_object: kwargs
    }
