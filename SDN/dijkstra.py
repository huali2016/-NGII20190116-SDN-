from collections import defaultdict
from heapq import *




class NodeMap:
    """\n
    初始化时传入一个参数，网络拓扑的二维邻接矩阵，例如\n
    net_topo = [\n
    [0, M, 10, M,  30, 100],\n
    [M, 0, 5,  M,  M,  M],\n
    [M, M, 0,  50, M,  M],\n
    [M, M, M,  0,  M,  10],\n
    [M, M, M,  20, 0,  60],\n
    [M, M, M,  M,  M,  0],\n
    ]\n
    注意要定义其中的 M=float('inf')，也就是正无穷大，代表2者之间不可达，对角线全为0，因为自己到自己的距离为0\n
    """
    def __init__(self,net_topo):
        self.topo=net_topo
        self.edges=[]

    def generate_edge_map(self,):
        M=float('inf')
        for i in range(len(self.topo)):
            for j in range(len(self.topo[0])):
                if i!=j and self.topo[i][j]!=M:
                    self.edges.append((i,j,self.topo[i][j]))    # self.edges 是三元组组成的list，三元组分别是起点序号i，终点序号j，距离k

    def dijkstra_raw(self, edges, from_node, to_node):
        g = defaultdict(list)
        for l,r,c in edges:
            g[l].append((c,r))
        q, seen = [(0,from_node,())], set()
        while q:
            (cost,v1,path) = heappop(q)
            if v1 not in seen:
                seen.add(v1)
                path = (v1, path)
                if v1 == to_node:
                    return cost,path
                for c, v2 in g.get(v1, ()):
                    if v2 not in seen:
                        heappush(q, (cost+c, v2, path))
        return float("inf"),[]

    def dijkstra(self,from_node,to_node):
        """\n
        该函数有2个参数， from_node代表起始节点号，to_node代表终点节点号，节点编号从0开始，依次递增0123456....\n
        该函数有2个返回值，分别代表从起点到终点的最短路径的长路，以及该最短路径依次经过的节点，节点用list形式表示，从list[0]遍历到节点末尾就代表依次经过的设备编号\n
        例如： \n
        length, Shortest_path = a.dijkstra(1,5)\n
        返回结果中：length =  65, Shortest_path = [1,2,3,5]\n
        代表最短距离是65，最短路径依次经过1,2,3,5\n
        """
        self.generate_edge_map()
        len_shortest_path = -1
        ret_path=[]
        length,path_queue = self.dijkstra_raw(self.edges, from_node, to_node)
        if len(path_queue)>0:
            len_shortest_path = length
            left = path_queue[0]
            ret_path.append(left)
            right = path_queue[1]
            while len(right)>0:
                left = right[0]
                ret_path.append(left)
                right = right[1]
            ret_path.reverse()
        return len_shortest_path,ret_path


if __name__ == '__main__':
    pass
