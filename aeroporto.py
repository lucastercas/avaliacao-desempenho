#!/usr/bin/env python

import simpy
import argparse
import random
import time

# Variaveis do aeroporto
num_pistas = 1
num_postos = 2
num_fingers = 2

# Variaveis da simulação
tmp_total = 50

# Variaveis dos avioes
tmp_espera = 5
tmp_md_pouso = 1
tmp_md_desembarque = 0.2
tmp_md_abastecimento = 0.2
tmp_md_decolagem = 1

# Metricas
total_avioes = 0
util_pista_pouso = 0
util_fingers = 0
util_postos = 0
util_pista_decolagem = 0

exponencial = lambda x: random.expovariate(1 / x)

def comecar_avioes(env):
    global total_avioes, tmp_espera
    while True:
        nv_aviao = Aviao(env, total_avioes)
        total_avioes += 1
        env.process(nv_aviao.run())
        yield env.timeout(exponencial(tmp_espera))

class Aviao(object):
    def __init__(self, env, idx):
        self.env = env
        self.idx = idx
        self.combustivel_atual = 10 # Porcentagem
        self.num_abastecimentos = 0
        self.tmp_solo = []
        self.util_finger = 0

    def run(self):
        global util_pista_pouso, util_pista_decolagem, util_fingers, util_postos
        while True:
            # Usar a pista pra pousar - fila 1
            with pista.request() as r_pista:
                if __debug__:
                    print(f'\nAviao {self.idx} - Esperando Pista Para Pousar ⌛ {self.env.now:.2f}')
                yield r_pista
                tmp = self.env.now # Calcular tempo de uso da pista para pouso
                yield self.env.process(self.usar_pista('pousar'))
                tmp = self.env.now - tmp
                util_pista_pouso += tmp

            tmp_solo = self.env.now # Calcular o tmp que o aviao fica em solo

            # Ponte de desembarque - fila 2
            with finger.request() as r_desembarque:
                yield r_desembarque
                tmp = self.env.now # Calcular tempo de uso do finger
                yield self.env.process(self.desembarque())
                tmp = self.env.now - tmp
                util_fingers += tmp

            # Se precisar abastecer - fila 3
            if(random.choice([0, 1]) is 0):
                with posto.request() as r_abastecimento:
                    yield r_abastecimento
                    tmp = self.env.now
                    yield self.env.process(self.abastecer())
                    tmp = self.env.now - tmp
                    util_postos += tmp

            # Usar a pista pra decolar - fila 4
            with pista.request() as r_pista:
                if __debug__:
                    print(f'\nAviao {self.idx} - Esperando Pista Para Decolar ⌛ {self.env.now:.2f}')
                yield r_pista
                tmp = self.env.now # Calcular tempo de uso da pista para desembarque
                yield self.env.process(self.usar_pista('decolar'))
                tmp = self.env.now - tmp
                util_pista_decolagem += tmp

            tmp_solo = self.env.now - tmp_solo
            self.tmp_solo.append(tmp_solo)

    def usar_pista(self, funcao):
        if funcao is 'pousar':
            if __debug__:
                print(f'Aviao {self.idx} - Pousando 🛬 {self.env.now:.2f}')
            yield self.env.timeout(exponencial(tmp_md_pouso))
        elif funcao is 'decolar':
            if __debug__:
                print(f'Aviao {self.idx} - Decolando 🛫 {self.env.now:.2f}')
            yield self.env.timeout(exponencial(tmp_md_decolagem))

    def desembarque(self):
        if __debug__:
            print(f'Aviao {self.idx} - Desembarcando 🚶 {self.env.now:.2f}')
        yield self.env.timeout(exponencial(tmp_md_desembarque))

    def abastecer(self):
        if __debug__:
            print(f'Aviao {self.idx} - Abastecendo ⛽ {self.env.now:.2f}')
        yield self.env.timeout(exponencial(tmp_md_abastecimento))

def main():
    global num_pistas, num_fingers, num_postos, tmp_espera

    parser = argparse.ArgumentParser(description='Simular um aeroporto. Ex: ./aeroporto.py --pistas 2 --postos 2 --fingers 2 --espera 5')

    parser.add_argument('--pistas', dest='pistas', required=True, help="Numero de pistas no aeroporto")
    parser.add_argument('--postos', dest='postos', required=True, help="Numero de postos de abastecimento no aeroporto")
    parser.add_argument('--fingers', dest='fingers', required=True, help="Numero de fingers no aeroporto")
    parser.add_argument('--espera', dest='espera', required=True, help="Tempo de espera entre chegadas de Avioes")

    args = parser.parse_args()
    num_pistas = int(args.pistas)
    num_fingers = int(args.fingers)
    num_postos = int(args.postos)
    tmp_espera = int(args.espera)

    seed = 10
    random.seed(seed)
    env = simpy.Environment()

# Recursos:
    global pista, finger, posto
    pista = simpy.Resource(env, capacity=num_pistas)
    finger = simpy.Resource(env, capacity=num_fingers)
    posto = simpy.Resource(env, capacity=num_postos)

    env.process(comecar_avioes(env))
    env.run(until=tmp_total)

    global util_pista_pouso, util_fingers, util_postos, util_pista_decolagem

    if __debug__:
        print( f'\nSistema:'
        f'\n\tTempo Total: {tmp_total}'
        f'\n\n\tNumero de Avioes: {total_avioes}'
        f'\n\tNúmero de Pistas: {num_pistas}'
        f'\n\tNumero de Fingers: {num_fingers}'
        f'\n\tNúmero de Postos de Abastecimento: {num_postos}'
        f'\n\tUtilização das Pistas Para Pouso: {util_pista_pouso}'
        f'\n\n\tUtilização dos Fingers: {util_fingers}'
        f'\n\tUtilização dos Postos: {util_postos}'
        f'\n\tUtilização das Pistas Para Decolagem: {util_pista_decolagem}'
        f'\n\tVazao: {total_avioes / tmp_total}'
        )
    else:
        print(f'{tmp_total},{total_avioes},{num_pistas},{util_pista_pouso:.2f},{util_pista_decolagem:.2f},{num_postos},{util_postos:.2f},{num_fingers},{util_fingers:.2f}')

if __name__ == "__main__":
    main()
