import networkx as nx
import numpy as np
import pandas as pd

def populate_route(route, k, G, router_weights=None):
    """Populate short routes with random neighbors"""
    path = route.copy()
    trial_cnt = 0
    max_trials = 10
    success = True
    target = route[-1].replace("_trg","")
    while len(path) < k+1:
        pos = np.random.choice(range(len(path)-1))
        n1, n2 = path[pos], path[pos+1]
        # find common directed neighbor
        neigh = set(G.successors(n1)).intersection(set(G.predecessors(n2)))
        if target in neigh:
            neigh.remove(target)
        # exclude loops
        neigh = list(neigh.difference(set(path)))
        if len(neigh) == 0:
            trial_cnt += 1
            if trial_cnt == max_trials:
                success = False
                break
            continue
        probas = None
        if router_weights != None:
            weights = np.array([float(router_weights.get(n, 0.0)) for n in neigh])
            sum_ = np.sum(weights)
            if sum_ > 0:
                 probas = weights / sum_
        new_node = np.random.choice(neigh, p=probas)
        path.insert(pos+1, new_node)
    # finalize the instance
    return success, tuple(path)

def calculate_cost(route, G):
    """Calculate transaction cost for the sender node"""
    s = 0.0
    # last edge has no routing cost
    for i in range(len(route)-2):
        n1, n2 = route[i], route[i+1]
        s += G[n1][n2]["total_fee"]
    return s

def validate_path(route, G):
    # all nodes are unique
    if len(set(route)) == len(route):
        # all links are present
        for i in range(len(route)-1):
            n1, n2 = route[i], route[i+1]
            valid = G.has_edge(n1, n2)
            if not valid:
                print("No edge: %s - %s" % (n1,n2))
                break
        return valid
    else:
        print("Node duplication!")
        return False 

def mix_routes(route_1, route_2, G):
    """Randomly select neighbors from other routes"""
    target = route_1[-1].replace("_trg","")
    res = []
    for i in range(1,len(route_1)-1):
        n1, n2 = route_1[i-1], route_1[i+1]
        neigh = set(G.successors(n1)).intersection(set(G.predecessors(n2)))
        neigh = neigh.difference(set(route_1))
        if target in neigh:
            neigh.remove(target)
        neigh = list(neigh.intersection(set(route_2[1:-1])))
        if len(neigh) > 0:
            r1 = list(route_1)
            r1[i] = np.random.choice(neigh)
            if not validate_path(r1, G):
                raise RuntimeError("Invalid path: %s" % r1)
            res.append(tuple(r1))
    return res

class GeneticPaymentRouter():
    def __init__(self, k, G, router_weights=None):
        self.k = k
        self.G = G
        self.router_weights = router_weights
        
    def _init_population(self, route, size):
        population = []
        for _ in range(size):
            success, path = populate_route(route, self.k, self.G, self.router_weights)
            if success:
                population.append(path)
        # remove duplications
        return list(set(population))
    
    def _eval_population(self, population):
        costs = [calculate_cost(item, self.G) for item in population]
        pop_df = pd.DataFrame(list(zip(population, costs)), columns=["route","cost"])
        opt_record = pop_df.nsmallest(1,"cost").values
        opt_path, opt_cost = opt_record[0,0], opt_record[0,1]
        return pop_df, opt_path, opt_cost
    
    def _gen_offsprings(self, pop_df, cnt, times=5):
        """Generate offsprings from best individuals. Additional random individuals are also sampled from the previous population"""
        individuals = list(pop_df["route"])
        N = len(individuals)
        parents = list(pop_df.nsmallest(cnt, "cost")["route"])
        L = len(parents)
        offsprings = []
        for _ in range(times):
            # random permutation
            np.random.shuffle(parents)
            # generate new offsprings pairwise
            for i in range(0,L-1,2):
                p1, p2 = parents[i], parents[i+1]
                offsprings += mix_routes(p1, p2, self.G)
                offsprings += mix_routes(p2, p1, self.G)
        unique_offsprings = list(set(offsprings))
        rnd_indices = set(np.random.choice(range(L), size=len(unique_offsprings), replace=True))
        return unique_offsprings + [individuals[j] for j in rnd_indices]
            
    def run(self, route, size=100, best_ratio=0.25, iterations=5, verbose=False):
        """Run fixed size minimal cost search with genetic algorithm"""
        pop = self._init_population(route, size)
        if len(pop) == 0:
            return calculate_cost(route, self.G), len(route)-1, route, -1
        else:
            pop_df, opt_path, opt_cost = self._eval_population(pop)
            if verbose:
                print("init", len(pop), opt_cost)
            for idx in range(iterations):
                pop = self._gen_offsprings(pop_df, int(size*best_ratio))
                if len(pop) == 0:
                    if verbose:
                        print("Empty population in %i round!" % (idx+1))
                    break
                pop_df, new_path, new_cost = self._eval_population(pop)
                if new_cost < opt_cost:
                    opt_cost = new_cost
                    opt_path = new_path
                else:
                    if verbose:
                        print("Early stopping in %i round!" % (idx+1))
                    break
                if verbose:
                    print(len(pop), new_cost)
            return opt_cost, len(opt_path)-1, opt_path, idx
