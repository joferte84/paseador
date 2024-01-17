from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def resolver_tsp(G, nodos):
    # Crear la matriz de distancias
    distancia_matrix = [[calcular_distancia_entre_nodos(G, i, j) for j in nodos] for i in nodos]

    # Crear el manager de rutas y el modelo de routing
    manager = pywrapcp.RoutingIndexManager(len(distancia_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Crear la función de distancia
    def distancia_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distancia_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distancia_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Configurar parámetros de búsqueda
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Resolver el problema
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None

    # Extraer la ruta
    index = routing.Start(0)
    ruta_optima = []
    while not routing.IsEnd(index):
        ruta_optima.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    ruta_optima.append(manager.IndexToNode(index))

    return ruta_optima
