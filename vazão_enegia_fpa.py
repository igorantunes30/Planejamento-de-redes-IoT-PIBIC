import numpy as np
import matplotlib.pyplot as plt

def fpa_optimization_lora(n=10, d=40, max_iter=10000, p=0.8):
    S_min = 7
    S_max = 12
    Nc_initial = 10
    Nc_final = 40
    lambda_val = 6
    b = 48
    Toa = np.array([0.1048, 0.1802, 0.3211, 0.5636, 1.0485, 1.9398])
    Trx1 = np.array([1.1048, 1.1802, 1.3211, 1.5636, 2.0485, 2.9398])
    Trx2 = np.array([2.1048, 2.1802, 2.3211, 2.5636, 3.0485, 3.9398])
    V = 3.3
    I_tx = 44
    I_rx = 10.5
    I_st = 1.4
    I_id = 0.0015
    RD1 = 1
    RD2 = 2
    T = 720
    n_sf = S_max - S_min + 1
    Nc_values = np.arange(Nc_initial, Nc_final + 1, 1)
    pesos = np.array([[1, 0]]) #, [0.75, 0.25], [0.5, 0.5], [0.25, 0.75], [0.1, 0.9]])
    labels = ['Peso (1,0)']#, 'Peso (0.75,0.25)', 'Peso (0.5,0.5)', 'Peso (0.25,0.75)', 'Peso (0.1,0.9)']

    plt.figure(figsize=(14, 12))

    for i, (pesoR, pesoE) in enumerate(pesos):
        vazao_total = []
        energia_total = []
        convergencia = []
        fitness_values = []

        for Nc in Nc_values:
            Rmax, Emin = flower_pollination_algorithm(lambda p: np.sum(utilidade_de_rede(lambda_val, p, Nc, b, Toa)), n_sf, n, max_iter, p, convergencia)
            Emax, Rmin = flower_pollination_algorithm(lambda p: np.sum(modelo_de_energia(V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, p, Nc, T, Toa)), n_sf, n, max_iter, p, convergencia, mode='minimize')

            alfa = Rmax - Rmin
            beta = Emax - Emin

            best_solution, best_fitness = flower_pollination_algorithm(lambda p: np.sum(eficiencia(lambda_val, p, Nc, b, Toa, V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, T, alfa, beta, pesoR, pesoE)), n_sf, n, max_iter, p, convergencia)

            vazao_atual = np.sum(vazao(lambda_val, best_solution, Nc, b, Toa))
            energia_atual = np.sum(modelo_de_energia(V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, best_solution, Nc, T, Toa))

            vazao_total.append(vazao_atual)
            energia_total.append(energia_atual)

        plt.subplot(3, 1, 1)
        plt.plot(Nc_values, vazao_total, '-o', label=labels[i])
        plt.title('Relação entre Número de Nós e Vazão Total para diferentes pesos')
        plt.xlabel('Número de Nós')
        plt.ylabel('Vazão Total (Throughput)')
        plt.grid(True)
        plt.legend()

        plt.subplot(3, 1, 2)
        plt.plot(Nc_values, energia_total, '-o', label=labels[i])
        plt.title('Relação entre Número de Nós e Energia Total para diferentes pesos')
        plt.xlabel('Número de Nós')
        plt.ylabel('Energia Total (J)')
        plt.grid(True)
        plt.legend()
        plt.subplot(3, 1, 3)
        plt.plot(fitness_values, 'r-', label=f"Variação Fitness Peso {pesoR}, {pesoE}")
        plt.plot(convergencia, 'o', label=f"Melhor Fitness Peso {pesoR}, {pesoE}")
        plt.title('Gráfico de Convergência do FPA para diferentes pesos')
        plt.xlabel('Iterações')
        plt.ylabel('Fitness')
        plt.grid(True)
        plt.legend()


    plt.tight_layout()
    plt.show()

def flower_pollination_algorithm(fitness_func, num_dimensions, pop_size, max_iter, p, convergencia, mode='maximize'):
    population = np.random.rand(pop_size, num_dimensions)
    population = population / population.sum(axis=1, keepdims=True)
    fitness = np.array([fitness_func(ind) for ind in population])

    if mode == 'maximize':
        best_fitness = np.max(fitness)
        best_solution = population[np.argmax(fitness)]
    else:
        best_fitness = np.min(fitness)
        best_solution = population[np.argmin(fitness)]

    convergencia.append(best_fitness)

    for _ in range(max_iter):
        for i in range(pop_size):
            if np.random.rand() > p:
                step = levy_flight(num_dimensions)
                new_solution = population[i] + step * (population[i] - best_solution)
            else:
                epsilon = np.random.rand()
                jk = np.random.choice(pop_size, 2, replace=False)
                new_solution = population[i] + epsilon * (population[jk[0]] - population[jk[1]])

            new_solution = np.clip(new_solution, 0, 1)
            new_solution /= new_solution.sum()

            new_fitness = fitness_func(new_solution)

            if (mode == 'maximize' and new_fitness > fitness[i]) or (mode == 'minimize' and new_fitness < fitness[i]):
                population[i] = new_solution
                fitness[i] = new_fitness

                if (mode == 'maximize' and new_fitness > best_fitness) or (mode == 'minimize' and new_fitness < best_fitness):
                    best_solution = new_solution
                    best_fitness = new_fitness

        convergencia.append(best_fitness)

    return best_solution, best_fitness

def trafego_de_carga(lambda_val, p, Nc, Toa):
    return lambda_val * p * Nc * Toa / 10000

def vazao(lambda_val, p, Nc, b, Toa):
    return lambda_val * p * Nc * b * np.exp(-2 * trafego_de_carga(lambda_val, p, Nc, Toa))

def modelo_de_energia(V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, p, Nc, T, Toa):
    return (0.5 * p * Nc * V * (Toa * I_tx + RD1 * I_st + Trx1 * I_rx) + 0.5 * p * Nc * V * (Toa * I_tx + (RD2 - Trx1) * I_st + (Trx1 + Trx2) * I_rx)) + (0.5 * p * Nc * V * (T - (Toa + Trx1 + RD1)) * I_id + 0.5 * p * Nc * V * (T - (Toa + RD2 + Trx2)) * I_id)

def utilidade_de_rede(lambda_val, p, Nc, b, Toa):
    return np.log(lambda_val * p * Nc * b) - 2 * trafego_de_carga(lambda_val, p, Nc, Toa)

def eficiencia(lambda_val, p, Nc, b, Toa, V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, T, alfa, beta, pesoR, pesoE):
    return (pesoR / alfa * utilidade_de_rede(lambda_val, p, Nc, b, Toa)) - (pesoE / beta * modelo_de_energia(V, I_id, I_st, I_tx, I_rx, Trx1, Trx2, RD1, RD2, p, Nc, T, Toa))

def levy_flight(num_dimensions):
    beta = 1.5
    sigma = (np.math.gamma(1 + beta) * np.sin(np.pi * beta / 2) / (np.math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
    u = np.random.randn(num_dimensions) * sigma
    v = np.random.randn(num_dimensions)
    step = u / np.abs(v) ** (1 / beta)
    return step

fpa_optimization_lora()
