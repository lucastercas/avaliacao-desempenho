#!/usr/bin/env python

import simpy
import argparse
import random
import time

# Variaveis dos avioes
tmp_md_pouso = 30
tmp_md_desembarque = 30
tmp_md_abastecimento = 30
tmp_md_decolagem = 30

exponencial = lambda x: random.expovariate(1 / x)

def comecar_avioes(env):
    global tmp_espera, num_avioes
    for i in range(num_avioes):
        nv_aviao = Aviao(env, i)
        env.process(nv_aviao.run())
        yield env.timeout(exponencial(tmp_espera))
    return 'end'

class Aviao(object):
    def __init__(self, env, idx):
        self.env = env
        self.idx = idx
        self.tmp_solo = 0
        self.tmp_aeroporto = 0

    def run(self):
        tmp_aeroporto = self.env.now
        if __debug__:
            print(f'{self.env.now:.2f} - Aviao {self.idx} - Chegou')

        global util_pista_pouso, util_pista_decolagem
        # Usar a pista pra pousar - fila 1
        yield self.env.process(self.usar_pista('pousar'))
        tmp_solo = self.env.now # Calcular o tmp que o aviao fica em solo

        # Ponte de desembarque - fila 2
        yield self.env.process(self.desembarque())
        # Se precisar abastecer - fila 3
        yield self.env.process(self.abastecer())
        # Usar a pista pra decolar - fila 4
        yield self.env.process(self.usar_pista('decolar'))

        self.tmp_solo = self.env.now - tmp_solo
        self.tmp_aeroporto = self.env.now - tmp_aeroporto

        if __debug__:
            print(f'{self.env.now:.2f} - Aviao {self.idx} - Saiu')

    def usar_pista(self, funcao):
        global util_pista_pouso, util_pista_decolagem
        if funcao is 'pousar':
            with pista.request() as r_pista:
                yield r_pista
                tmp = self.env.now
                yield self.env.timeout(exponencial(tmp_md_pouso))
                tmp = self.env.now - tmp
                util_pista_pouso += tmp
        elif funcao is 'decolar':
            with pista.request() as r_pista:
                yield r_pista
                tmp = self.env.now
                yield self.env.timeout(exponencial(tmp_md_decolagem))
                tmp = self.env.now - tmp
                util_pista_decolagem += tmp

    def desembarque(self):
        global util_fingers
        with finger.request() as r_desembarque:
            yield r_desembarque
            tmp = self.env.now
            yield self.env.timeout(exponencial(tmp_md_desembarque))
            tmp = self.env.now - tmp
            util_fingers += tmp

    def abastecer(self):
        global util_postos
        if(random.choice([0, 1]) is 0):
            with posto.request() as r_abastecimento:
                tmp = self.env.now
                yield r_abastecimento
                yield self.env.timeout(exponencial(tmp_md_abastecimento))
                tmp = self.env.now - tmp
                util_postos += tmp

def main():
    seed = 10
    random.seed(seed)
    env = simpy.Environment()

    parser = argparse.ArgumentParser(description='Simular um aeroporto. Ex: ./aeroporto.py --pistas 2 --postos 2 --fingers 2 --espera 5')
    parser.add_argument('--pistas', dest='pistas', required=False, help="Numero de pistas no aeroporto")
    parser.add_argument('--postos', dest='postos', required=False, help="Numero de postos de abastecimento no aeroporto")
    parser.add_argument('--fingers', dest='fingers', required=False, help="Numero de fingers no aeroporto")
    parser.add_argument('--espera', dest='espera', required=False, help="Tempo de espera entre chegadas de Avioes")
    args = parser.parse_args()

    # Parametros do Sistema
    global num_pistas, num_fingers, num_postos
    num_pistas = int(args.pistas) if args.pistas else 1
    num_fingers = int(args.fingers) if args.fingers else 2
    num_postos = int(args.postos) if args.postos else 2

    # Carga de Trabalho
    global tmp_espera, num_avioes
    num_avioes = 10
    tmp_espera = int(args.espera) if args.espera else 30

    # Metricas
    global util_pista_pouso, util_fingers, util_postos, util_pista_decolagem
    util_pista_pouso = 0
    util_fingers = 0
    util_postos = 0
    util_pista_decolagem = 0

    # Recursos:
    global pista, finger, posto
    pista = simpy.Resource(env, capacity=num_pistas)
    finger = simpy.Resource(env, capacity=num_fingers)
    posto = simpy.Resource(env, capacity=num_postos)


    sim = env.process(comecar_avioes(env))
    print(env.events.PENDING)
    env.run()
    tmp_total = env.now

    #print(f'{tmp_total:.2f},{num_avioes},{num_pistas},{util_pista_pouso/tmp_total:.2f},{util_pista_decolagem/tmp_total:.2f},{((util_pista_pouso+util_pista_decolagem)/tmp_total):.2f},{num_postos},{util_postos/tmp_total:.2f},{num_fingers},{util_fingers/tmp_total:.2f}')
    print(f'{tmp_total:.2f},{num_pistas},{num_fingers},{num_postos}')

if __name__ == "__main__":
    main()
