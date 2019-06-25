#!/usr/bin/env python

import random
import math
import simpy
import argparse
import matplotlib.pyplot as plt
import numpy as np

def tamanhoDoc():
    r = random.random()
    if r < 0.35:
        return 0.8
    if r < 0.85:
        return 5.5
    if r < 0.99:
        return 80
    return 800


class Web(object):
    def __init__(self, env, tempoDisco=6, taxaAcerto=0.25):
        self.env = env
        # Parametros Net:
        self.larguraBandaLan = 10 #Mbps
        self.ovhdFrame = 18 # Overhead do Frame
        self.ovhdTCP =  20 # Overhead do TCP
        self.ovhdIP = 20 # Overhead do IP
        self.mss = 1460 # Maximum Segment Size TCP (bytes)
        self.latenciaRoteador = 50 #us/pacote
        self.larguraBandaLink = 56 #Kbps
        self.rtt  = 100 #ms
        self.taxaDadosInternet = 20 #Kbps
        self.taxaBrowser = 0.3 #req/set
        self.porcentagemAtiva = 0.1
        self.reqHttpMedia = 100 #bytes

        # Parametros Proxy:
        self.taxaAcerto = taxaAcerto
        self.tempoAcertoCPU = 0.25 #ms
        self.tempoFaltaCPU = 0.5 #ms
        self.tempoDisco = tempoDisco #ms/Kb lido

        # Recursos
        self.resourceLan = simpy.Resource(env, 1)
        self.resourceOutputLink = simpy.Resource(env, 1)
        self.resourceInputLink = simpy.Resource(env, 1)
        #self.cpuResource = simpy.Resource()
        #self.discoResource = simpy.Resource()

    def quantDatagrams(self, mensagem):
        return mensagem / self.mss

    def overhead(self, mensagem):
        return self.quantDatagrams(mensagem) * (self.ovhdTCP + self.ovhdIP + self.ovhdFrame)

    def tempoRede(self, mensagem, largura):
        return 8 * (mensagem + self.overhead(mensagem)) / (1000000 * largura)

    # Fila 2 -> 3
    def requestLan(self):
        yield self.env.timeout( self.tempoRede(self.reqHttpMedia, self.larguraBandaLan))

    # Fila 3 -> 4
    def requestRouter(self):
        yield self.env.timeout(self.latenciaRoteador / 1000000)

    # Fila 4 -> 5
    def linkOutput(self):
        yield self.env.timeout(self.tempoRede(self.reqHttpMedia, self.larguraBandaLink) + 3 * self.tempoRede(0.0001, self.larguraBandaLink))

    # Fila 5 -> 6
    def isp(self, tamDoc):
        yield self.env.timeout((2 * self.rtt / 1000) + (tamDoc / self.taxaDadosInternet))

    # Fila 6 -> 3
    def linkInput(self, tamDoc):
        yield self.env.timeout(self.tempoRede(tamDoc, self.larguraBandaLink) + 2 * self.tempoRede(0.0001, self.larguraBandaLink))

    # Fila 3 -> 2
    def responseRouter(self, tamDoc):
        yield self.env.timeout( (self.quantDatagrams(1204 * tamDoc) + 6) * self.latenciaRoteador * 0.000001)

    # Fila 2 -> 1
    def responseLan(self, tamDoc):
        yield self.env.timeout(self.tempoRede(1024 * tamDoc, self.larguraBandaLan))

    # Fila 8 -> 7 (tanto hit qnt miss)
    def disco(self, tamDoc):
        pass
        #yield self.env.timeout(tempoDisco * tamDoc/1000)

    def cpu(self):
        pass

def cliente(env, nome, web):
    LAN_REQUEST_WAIT_TIME = 0
    LAN_REQUEST_SERVICE_TIME = 0
    ROUTER_REQUEST_SERVICE_TIME = 0
    OUTPUT_LINK_WAIT_TIME = 0
    OUTPUT_LINK_SERVICE_TIME = 0
    ISP_SERVICE_TIME = 0
    INPUT_LINK_WAIT_TIME = 0
    INPUT_LINK_SERVICE_TIME = 0
    ROUTER_RESPONSE_SERVICE_TIME = 0
    LAN_RESPONSE_WAIT_TIME = 0
    LAN_RESPONSE_SERVICE_TIME = 0

    tamDoc = tamanhoDoc()
    #print(f'{env.now:.2f}: {nome}[entrada]')

    startWait = env.now
    with web.resourceLan.request() as resourceLan:
        yield resourceLan
        LAN_REQUEST_WAIT_TIME += env.now - startWait
        startService = env.now
        yield env.process(web.requestLan())
        LAN_REQUEST_SERVICE_TIME += env.now - startService

    startService = env.now
    yield env.process(web.requestRouter())
    ROUTER_REQUEST_SERVICE_TIME += env.now - startService

    startWait = env.now
    with web.resourceOutputLink.request() as resourceOutputLink:
        yield resourceOutputLink
        OUTPUT_LINK_WAIT_TIME += env.now - startWait
        startService = env.now
        yield env.process(web.linkOutput())
        OUTPUT_LINK_SERVICE_TIME += env.now - startService

    startService = env.now
    yield env.process(web.isp(tamDoc))
    ISP_SERVICE_TIME += env.now - startService

    startWait = env.now
    with web.resourceInputLink.request() as resourceInputLink:
        yield resourceInputLink
        INPUT_LINK_WAIT_TIME += env.now - startWait
        startService = env.now
        yield env.process(web.linkInput(tamDoc))
        INPUT_LINK_SERVICE_TIME += env.now - startService

    startService = env.now
    yield env.process(web.responseRouter(tamDoc))
    ROUTER_RESPONSE_SERVICE_TIME += env.now - startService

    startWait = env.now
    with web.resourceLan.request() as resourceLan:
        yield resourceLan
        LAN_RESPONSE_WAIT_TIME += env.now - startWait
        startService = env.now
        yield env.process(web.responseLan(tamDoc))
        LAN_RESPONSE_SERVICE_TIME += env.now - startService

    TOTAL_TIME = LAN_REQUEST_WAIT_TIME + LAN_REQUEST_SERVICE_TIME + ROUTER_REQUEST_SERVICE_TIME +OUTPUT_LINK_WAIT_TIME + OUTPUT_LINK_SERVICE_TIME + ISP_SERVICE_TIME + INPUT_LINK_WAIT_TIME + INPUT_LINK_SERVICE_TIME + ROUTER_RESPONSE_SERVICE_TIME + LAN_RESPONSE_WAIT_TIME+ LAN_RESPONSE_SERVICE_TIME

def plot(xlabel, ylabel):
    plt.plot([1, 2, 3, 4])
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)

    plt.show()

def run(env, taxaAcerto, tempoDisco, numClientes):
    web = Web(env, tempoDisco, taxaAcerto)
    for i in range(numClientes):
        env.process(cliente(env, i, web))
        yield env.timeout(0.2)

def setup(taxaAcerto):
    numClientes = 20
    tempoDisco = 6
    numSimulations = 5

    TOTAL_TX_PROCESSAMENTO = 0
    TOTAL_SIM_TIME= 0
    for i in range(numSimulations):
        random.seed()
        env = simpy.Environment()
        print(f'## Simulacao: {i} ##')

        startSimulation = env.now
        env.process(run(env, taxaAcerto, tempoDisco, numClientes))
        env.run()
        simTime = env.now - startSimulation
        print(f'\tSim Time: {simTime}')

        TOTAL_SIM_TIME += simTime
        TOTAL_TX_PROCESSAMENTO += numClientes / simTime

    MD_SIM_TIME = TOTAL_SIM_TIME / numSimulations
    MD_TX_PROCESSAMENTO = TOTAL_TX_PROCESSAMENTO / numSimulations

    print(f"Md Sim Time: {MD_SIM_TIME}")
    print(f'Md Req/s: {MD_TX_PROCESSAMENTO}')

def main():
    # Parse the Arguments
    parser = argparse.ArgumentParser(description='Description')
    parser.add_argument('--acerto', metavar='taxa_acerto', type=float, help="Taxa de acerto do cache", default=0.5)
    args = parser.parse_args()
    #taxa_acerto = args.acerto
    taxaAcerto = 0.25
    numClientes = 150


    setup(taxaAcerto)

    # Setup matplotlib
    params = {
        'ylabel': 'Tempo de Processamento',
        'xlabel': 'Tempo de Serviço Disco (ms/Kb lido)'
    }
    #plot(**params)

if __name__ == "__main__":

    print('===== Beginning Simulation =====')
    main()

