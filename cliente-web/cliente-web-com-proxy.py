#!/usr/bin/env python

import random
import math
import simpy

from web import Web
from graphic import plot_all, plot_each

def tamanhoDoc():
    r = random.random()
    if r < 0.35:
        return 0.8
    if r < 0.85:
        return 5.5
    if r < 0.99:
        return 80
    return 800

def cliente(env, nome, web, taxaAcerto):
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

    CPU_WAIT_TIME = 0
    CPU_SERVICE_TIME = 0
    DISCO_WAIT_TIME = 0
    DISCO_SERVICE_TIME = 0

    hit = True if random.random() < taxaAcerto else False

    tamDoc = tamanhoDoc()

    # Fila 1 -> 2 (cliente -> lan) de pedido
    startWait = env.now
    with web.resourceLan.request() as resourceLan:
        yield resourceLan
        LAN_REQUEST_WAIT_TIME += env.now - startWait
        startService = env.now
        yield env.process(web.requestLan())
        LAN_REQUEST_SERVICE_TIME += env.now - startService

    if hit:
        # Fila 2 -> 7 (lan -> cpu)
        startWait = env.now
        with web.cpuResource.request() as resourceCPU:
            yield resourceCPU
            CPU_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.cpuHit())
            CPU_SERVICE_TIME += env.now - startService

        # Fila 7 -> 8 (cpu -> disco)
        startWait = env.now
        with web.discoResource.request() as resourceDisco:
            yield resourceDisco
            DISCO_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.disco(tamDoc))
            DISCO_SERVICE_TIME += env.now - startService

        # Fila 7 -> 2 (proxy -> lan) de resposta
        startWait = env.now
        with web.resourceLan.request() as resourceLan:
            yield resourceLan
            LAN_RESPONSE_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.responseLan(tamDoc))
            LAN_RESPONSE_SERVICE_TIME += env.now - startService

    else:
        # Fila 2 -> 7 (lan -> cpu)
        startWait = env.now
        with web.cpuResource.request() as resourceCPU:
            yield resourceCPU
            CPU_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.cpuMiss())
            CPU_SERVICE_TIME += env.now - startService

        # Fila 7 -> 8 (cpu -> disco)
        startWait = env.now
        with web.discoResource.request() as resourceDisco:
            yield resourceDisco
            DISCO_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.disco(tamDoc))
            DISCO_SERVICE_TIME += env.now - startService

        # Fila 7 -> 2 (proxy -> lan) de pedido
        startWait = env.now
        with web.resourceLan.request() as resourceLan:
            yield resourceLan
            LAN_REQUEST_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.requestLan())
            LAN_REQUEST_SERVICE_TIME += env.now - startService

        # Fila 2 -> 3 (lan -> roteador)
        with web.resourceLan.request() as resourceLan:
            yield resourceLan
            LAN_REQUEST_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.requestLan())
            LAN_REQUEST_SERVICE_TIME += env.now - startService
            startService = env.now
            yield env.process(web.requestRouter())
            ROUTER_REQUEST_SERVICE_TIME += env.now - startService

        # Fila 3 -> 4(roteador -> saida)
        startWait = env.now
        with web.resourceOutputLink.request() as resourceOutputLink:
            yield resourceOutputLink
            OUTPUT_LINK_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.linkOutput())
            OUTPUT_LINK_SERVICE_TIME += env.now - startService

        # Fila 4 -> 5 (saida -> isp)
        startService = env.now
        yield env.process(web.isp(tamDoc))
        ISP_SERVICE_TIME += env.now - startService

        # Fila 5 -> 6 (isp -> entrada)
        startWait = env.now
        with web.resourceInputLink.request() as resourceInputLink:
            yield resourceInputLink
            INPUT_LINK_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.linkInput(tamDoc))
            INPUT_LINK_SERVICE_TIME += env.now - startService

        # Fila 6 -> 3 (saida -> roteador)
        startService = env.now
        yield env.process(web.responseRouter(tamDoc))
        ROUTER_RESPONSE_SERVICE_TIME += env.now - startService

        # Fila 3 -> 2 (roteador -> lan) de resposta
        startWait = env.now
        with web.resourceLan.request() as resourceLan:
            yield resourceLan
            LAN_RESPONSE_WAIT_TIME += env.now - startWait
            startService = env.now
            yield env.process(web.responseLan(tamDoc))
            LAN_RESPONSE_SERVICE_TIME += env.now - startService

    global tmp_resp
    tmp_resp += LAN_REQUEST_WAIT_TIME + LAN_REQUEST_SERVICE_TIME + ROUTER_REQUEST_SERVICE_TIME +OUTPUT_LINK_WAIT_TIME + OUTPUT_LINK_SERVICE_TIME + ISP_SERVICE_TIME + INPUT_LINK_WAIT_TIME + INPUT_LINK_SERVICE_TIME + ROUTER_RESPONSE_SERVICE_TIME + LAN_RESPONSE_WAIT_TIME+ LAN_RESPONSE_SERVICE_TIME + CPU_SERVICE_TIME + CPU_WAIT_TIME + DISCO_SERVICE_TIME + DISCO_WAIT_TIME

def setup(env, taxaAcerto, tempoDisco, numClientes):
    web = Web(env, tempoDisco, taxaAcerto)
    for i in range(numClientes):
        env.process(cliente(env, i, web, taxaAcerto))
        yield env.timeout(0.2)

def media2(txAcerto, tmpServDisco, nClientes, nSims):
    sum_md_tmp_resp = 0
    sum_md_tx_proc = 0
    for sim in range(nSims):
        global tmp_resp
        tmp_resp = 0

        # resetar seed, criar novo env
        random.seed()
        env = simpy.Environment()

        start_sim = env.now
        env.process(setup(env, txAcerto, tmpServDisco, nClientes))
        env.run()

        sim_time = env.now - start_sim
        md_tmp_resp = tmp_resp / nClientes
        md_tx_proc = nClientes / sim_time

        sum_md_tmp_resp += md_tmp_resp
        sum_md_tx_proc += md_tx_proc

    return sum_md_tmp_resp / nSims, sum_md_tx_proc / nSims

def media1(txAcerto, tmpServDisco, nClientes, nSims=10, nTries = 3):

    sum_tmp_resp = 0
    sum_tx_proc = 0

    for trie in range(nTries):
        tmp_resp, tx_proc = media2(txAcerto, tmpServDisco, nClientes, nSims)

        sum_tmp_resp += tmp_resp
        sum_tx_proc += tx_proc

    return sum_tmp_resp / nTries, sum_tx_proc / nTries

def main():
    nClientes = 150
    nSims = 30

    tmps_disco = [14, 10, 6, 2]
    txs_acerto = [0.2, 0.4, 0.6, 0.8]

    for tmpServDisco in tmps_disco:
        tmps_resp = []
        txs_proc = []

        for txAcerto in txs_acerto:

            tmp_resp, tx_proc = media1(txAcerto, tmpServDisco, nClientes, 10, 3)

            tmps_resp.append(tmp_resp)
            txs_proc.append(tx_proc)

        plot_each(f"Tempo de Disco: {tmpServDisco}",
                  "Taxa de Processamento (req/s)", txs_proc,
                  "Taxa de Acerto", txs_acerto,
                  f"disco_{tmpServDisco}-tx_proc-tx_acerto.png")

        plot_each(f"Tempo de Disco: {tmpServDisco}",
                  "Tempo de Resposta (s/req)", tmps_resp,
                  "Taxa de Acerto", txs_acerto,
                  f"disco_{tmpServDisco}-tpms_resp-tx_acerto.png")

    #plot_all("Comparacao Tempo de Disco",
             #"Tempo de Resposta (s/req)", ALL_TMP_RESPOSTA,
             #"Taxa de Acerto", TXS_ACERTO,
             #f"disco_all-tmpReposta-txAcerto.png",
             #TMPS_DISCO)
    #plot_all("Comparacao Tempo de Disco",
             #"Taxa de Processamento (req/s)", ALL_TXS_PROCESSAMENTO,
             #"Taxa de Acerto", TXS_ACERTO,
             #f"disco_all-txProcessamento-txAcerto.png",
             #TMPS_DISCO)

if __name__ == "__main__":
    print('\n#===== BEGIN Simulation =====#')
    main()
    print('\n#===== END Simulation =====#')

