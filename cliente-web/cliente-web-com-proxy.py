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
    global sum_tmp_resp, sum_roteador, sum_cpu, sum_disco, sum_entrada, sum_saida

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

    roteador = ROUTER_REQUEST_SERVICE_TIME + ROUTER_RESPONSE_SERVICE_TIME
    cpu = CPU_WAIT_TIME + CPU_SERVICE_TIME
    disco = DISCO_SERVICE_TIME + DISCO_WAIT_TIME
    entrada = INPUT_LINK_WAIT_TIME + INPUT_LINK_SERVICE_TIME
    saida = OUTPUT_LINK_WAIT_TIME + OUTPUT_LINK_SERVICE_TIME

    sum_roteador += roteador
    sum_cpu += cpu
    sum_disco += disco
    sum_entrada += entrada
    sum_saida += saida

    tmp_resp = LAN_REQUEST_WAIT_TIME + LAN_REQUEST_SERVICE_TIME + ROUTER_REQUEST_SERVICE_TIME +OUTPUT_LINK_WAIT_TIME + OUTPUT_LINK_SERVICE_TIME + ISP_SERVICE_TIME + INPUT_LINK_WAIT_TIME + INPUT_LINK_SERVICE_TIME + ROUTER_RESPONSE_SERVICE_TIME + LAN_RESPONSE_WAIT_TIME+ LAN_RESPONSE_SERVICE_TIME + CPU_SERVICE_TIME + CPU_WAIT_TIME + DISCO_SERVICE_TIME + DISCO_WAIT_TIME
    sum_tmp_resp += tmp_resp

def setup(env, tx_acerto, tmp_disco, n_clientes, largura_banda_link=56):
    web = Web(env, tmp_disco, tx_acerto, largura_banda_link)
    for i in range(n_clientes):
        env.process(cliente(env, i, web, tx_acerto))
        yield env.timeout(0.1)

def media2(txAcerto, tmpServDisco, nClientes, largura_banda_link, nSims):

    sum_md_tmp_resp = 0
    sum_tx_proc = 0

    for sim in range(nSims):
        global sum_tmp_resp
        sum_tmp_resp = 0

        # resetar seed, criar novo env
        random.seed()
        env = simpy.Environment()
        start_sim = env.now
        env.process(setup(env, txAcerto, tmpServDisco, nClientes, largura_banda_link))
        env.run() # RODAR ESSA SIMULACAO

        # tempo dessa simulacao
        sim_time = env.now - start_sim
        #md dos tmp de resp de cada req
        md_tmp_resp = sum_tmp_resp / nClientes
        # tx de proc dessa sim
        tx_proc = nClientes / sim_time

        # somar, pra depois tirar a media
        sum_md_tmp_resp += md_tmp_resp
        sum_tx_proc += tx_proc

    # media das <nsims> simulacoes
    md_tmp_resp = sum_md_tmp_resp / nSims
    md_tx_proc = sum_tx_proc / nSims

    return md_tmp_resp, md_tx_proc

def media1(txAcerto, tmpServDisco, nClientes, largura_banda_link, nSims=10, nTries = 3):

    sum_tmp_resp = 0
    sum_tx_proc = 0
    # vetores usados pra calcular a variancia
    tmps_resp = []
    txs_proc = []

    for media in range(nTries):
        tmp_resp, tx_proc = media2(txAcerto, tmpServDisco, nClientes, largura_banda_link, nSims)
        sum_tmp_resp += tmp_resp #somar o tpm de resp das medias
        sum_tx_proc += tx_proc #somar a tx de proc das medias

        tmps_resp.append(tmp_resp)
        txs_proc.append(tx_proc)

    # media das medias
    md_tmp_resp = sum_tmp_resp / nTries
    md_tx_proc = sum_tx_proc / nTries

    # calcular a variancia
    var_tmp_resp = 0
    for resp in tmps_resp:
        var_tmp_resp += (resp - md_tmp_resp)**2
    var_tmp_resp /= nTries
    var_tx_proc = 0
    for proc in txs_proc:
        var_tx_proc += (proc - md_tx_proc)**2
    var_tx_proc /= nTries

    return md_tmp_resp, md_tx_proc, var_tmp_resp, var_tx_proc

def run(tmp_serv_disco, txs_acerto, quest_dir, largura_banda_link=56):
    nClientes = 150
    nSims = 30

    tmps_resp = []
    txs_proc = []

    for tx_acerto in txs_acerto:
        tmp_resp, tx_proc, var_tmp_resp, var_tx_proc = media1(tx_acerto, tmp_serv_disco, nClientes, largura_banda_link, 10, 3)
        tmps_resp.append(tmp_resp)
        txs_proc.append(tx_proc)

    # TODO: como mostrar a variancia?
    #print(f"Var Tmp Resp: {var_tmp_resp}")
    #print(f"Var Tx Proc: {var_tx_proc}")

    plot_each(f"Tempo de Disco: {tmp_serv_disco}",
              "Taxa de Processamento (req/s)", txs_proc,
              "Taxa de Acerto", txs_acerto,
              f"{quest_dir}/each/disco_{tmp_serv_disco}-tx_proc-tx_acerto.png")

    plot_each(f"Tempo de Disco: {tmp_serv_disco}",
              "Tempo de Resposta (s/req)", tmps_resp,
              "Taxa de Acerto", txs_acerto,
              f"{quest_dir}/each/disco_{tmp_serv_disco}-tpm_resp-tx_acerto.png")
    return tmps_resp, txs_proc

# variacao de req/s e de s/req em funcao da tx de acerto
# qual eh o gargalo?
def primeiro_cenario():
    tmps_disco = [14, 10, 6, 2]
    txs_acerto = [0.2, 0.4, 0.6, 0.8]

    # Tempo de Disco:
    all_tmps_resp = []
    all_txs_proc = []
    for tmp_serv_disco in tmps_disco:
        tmps_resp, txs_proc = run(tmp_serv_disco, txs_acerto, "quest-1")
        all_tmps_resp.append(tmps_resp)
        all_txs_proc.append(txs_proc)

    plot_all("Comparacao Tempo de Disco",
             "Tempo de Resposta (s/req)", all_tmps_resp,
             "Taxa de Acerto", txs_acerto,
             f"quest-1/disco_all-tmp_resp-tx_acerto.png",
             tmps_disco)
    plot_all("Comparacao Tempo de Disco",
             "Taxa de Processamento (req/s)", all_txs_proc,
             "Taxa de Acerto", txs_acerto,
             f"quest-1/disco_all-tx_proc-tx_acerto.png",
             tmps_disco)

# larguraBandaLink vai pra 1544, tx_acerto 0.4:
# como fica a tx de proc e o tmp de resp?
# qual eh o gargalo?
def segundo_cenario():
    #segundo_cenario_1()
    segundo_cenario_2()

def segundo_cenario_2():
    tmps_disco = [6, 4, 2, 1]
    largura_banda_link = 1544
    largura_banda_link_inicial = 56

    n_clientes = 150

    for tmp_serv_disco in tmps_disco:
        print(f"Tmp Serv Disco: {tmp_serv_disco}")
        random.seed()

        env = simpy.Environment()
        start_time = env.now
        env.process(setup(env, 0.4, tmp_serv_disco, n_clientes, largura_banda_link_inicial))
        env.run()

        sim_time = env.now - start_time

        tx_proc = n_clientes / sim_time
        print(f"Taxa de Processamento: {tx_proc} req/s")

    for tmp_serv_disco in tmps_disco:
        print(f"Tmp Serv Disco: {tmp_serv_disco}")
        random.seed()

        env = simpy.Environment()
        start_time = env.now
        env.process(setup(env, 0.4, tmp_serv_disco, n_clientes, largura_banda_link))
        env.run()

        sim_time = env.now - start_time

        tx_proc = n_clientes / sim_time
        print(f"Taxa de Processamento: {tx_proc} req/s")

def segundo_cenario_1():
    tx_acerto = [0.2, 0.4, 0.6, 0.8]
    largura_banda_link = 1544
    largura_banda_link_inicial = 56
    tmp_serv_disco = 6
    n_clientes = 150

    global sum_tmp_resp, sum_roteador, sum_cpu, sum_disco, sum_entrada, sum_saida
    sum_tmp_resp = 0
    sum_roteador = 0
    sum_cpu = 0
    sum_disco = 0
    sum_entrada = 0
    sum_saida = 0

    random.seed()
    env = simpy.Environment()
    env.process(setup(env, 0.4, 6, 150, largura_banda_link))
    env.run()

    print(f"\nRoteador: {sum_roteador/n_clientes}")
    print(f"CPU: {sum_cpu/n_clientes}")
    print(f"Disco: {sum_disco/n_clientes}")
    print(f"Entrada: {sum_entrada/n_clientes}")
    print(f"Saida: {sum_saida/n_clientes}")

    sum_tmp_resp = 0
    sum_roteador = 0
    sum_cpu = 0
    sum_disco = 0
    sum_entrada = 0
    sum_saida = 0

    random.seed()
    env = simpy.Environment()
    env.process(setup(env, 0.4, 6, 150, largura_banda_link_inicial))
    env.run()

    print(f"\nRoteador: {sum_roteador/n_clientes}")
    print(f"CPU: {sum_cpu/n_clientes}")
    print(f"Disco: {sum_disco/n_clientes}")
    print(f"Entrada: {sum_entrada/n_clientes}")
    print(f"Saida: {sum_saida/n_clientes}")

def main():
    global sum_tmp_resp, sum_roteador, sum_cpu, sum_disco, sum_entrada, sum_saida
    sum_tmp_resp = 0
    sum_roteador = 0
    sum_cpu = 0
    sum_disco = 0
    sum_entrada = 0
    sum_saida = 0
    #primeiro_cenario()
    segundo_cenario()

if __name__ == "__main__":
    print('\n#===== BEGIN Simulation =====#')
    main()
    print('\n#===== END Simulation =====#')

