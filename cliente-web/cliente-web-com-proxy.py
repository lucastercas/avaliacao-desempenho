#!/usr/bin/env python

import random
import math
import simpy
import argparse
import matplotlib.pyplot as plt
import numpy as np

# Parametros:
larguraBandaLan = 10 #Mbps
ovhdFrame = 18 # Overhead do Frame
mss = 1460 # Maximum Segment Size TCP (bytes)
latenciaRoteador = 50 #us/pacote
larguraBandaLink = 56 #Kbps
rtt  = 100 #ms
taxaDadosInternet = 20 #Kbps
taxaBrowser = 0.3 #req/set
numClientes = 150
porcentagemAtiva = 0.1
reqHttpMedia = 100 #bytes

# Parametros Proxy:
tempoAcertoCPU = 0.25 #ms
tempoFaltaCPU = 0.5 #ms
tempoDisco = 6 #ms/Kb lido

def tamanhoDoc():
    r = random.random()
    if r < 0.35:
        return 0.8
    if r < 0.85:
        return 5.5
    if r < 0.99:
        return 80
    return 800

def quantDatagrams(mensagem):
    return mensagem / mss

def overhead(mensagem):
    ovhdTCP =  20 # Overhead do TCP
    ovhdIP = 20 # Overhead do IP
    return quantDatagrams(mensagem) * (ovhdTCP + ovhdIP + ovhdFrame)

def tempoRede(mensagem, largura):
    return 8 * (mensagem + overhead(mensagem)) / (1000000 * largura)

class Web(object):
    def __init__(self, env, numLan, numLinkSaida, numLinkEntrada):
        self.env = env
        self.resourceLan = simpy.Resource(env, numLan)
        self.resourceOutputLink = simpy.Resource(env, numLinkSaida)
        self.resourceInputLink = simpy.Resource(env, numLinkEntrada)
        #self.cpuResource = simpy.Resource()
        #self.discoResource = simpy.Resource()

    # Fila 2 -> 3
    def requestLan(self):
        yield self.env.timeout(tempoRede(reqHttpMedia, larguraBandaLan))

    # Fila 3 -> 4
    def requestRouter(self):
        yield self.env.timeout(latenciaRoteador / 1000000)

    # Fila 4 -> 5
    def linkOutput(self):
        yield self.env.timeout(tempoRede(reqHttpMedia, larguraBandaLink) + 3 * tempoRede(0.0001, larguraBandaLink))

    # Fila 5 -> 6
    def isp(self, tamDoc):
        yield self.env.timeout((2 * rtt / 1000) + (tamDoc / taxaDadosInternet))

    # Fila 6 -> 3
    def linkInput(self, tamDoc):
        yield self.env.timeout(tempoRede(tamDoc, larguraBandaLink) + 2 * tempoRede(0.0001, larguraBandaLink))

    # Fila 3 -> 2
    def responseRouter(self, tamDoc):
        yield self.env.timeout( (quantDatagrams(1204 * tamDoc) + 6) * latenciaRoteador * 0.000001)

    # Fila 2 -> 1
    def responseLan(self, tamDoc):
        yield self.env.timeout(tempoRede(1024 * tamDoc, larguraBandaLan))

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
    print(f'{env.now:.2f}: {nome}[entrada]')

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

    print(f'{env.now:.2f}: {nome}[saida]')

def setup_clients(env, web):
    numClientes = 0
    while 1:
        yield env.timeout(0.2)
        env.process(cliente(env, numClientes, web))
        numClientes += 1

def run(taxa_acerto):
    num_lan = 1
    num_link_saida = 1
    num_link_entrada = 1
    sim_time = 10
    # Set up the env:
    env = simpy.Environment()
    web = Web(env, num_lan, num_link_saida, num_link_entrada)
    # Set up the clients:
    env.process(setup_clients(env, web))
    # Run simulation
    env.run(until = sim_time)

def main():
    # Parse the Arguments
    parser = argparse.ArgumentParser(description='Description')
    parser.add_argument('--acerto', metavar='taxa_acerto', type=float, help="Taxa de acerto do cache", default=0.5)
    args = parser.parse_args()
    print(args)

    print('===== Beginning Simulation =====')
    # Setup matplotlib

    taxa_acerto = args.acerto
    #run(taxa_acerto)

print('iae')
if __name__ == "__main__":
    main()

