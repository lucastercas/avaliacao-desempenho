import simpy

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
        self.taxaAcerto = taxaAcerto

        # Recursos
        self.resourceLan = simpy.Resource(env, 1)
        self.resourceOutputLink = simpy.Resource(env, 1)
        self.resourceInputLink = simpy.Resource(env, 1)
        self.cpuResource = simpy.Resource(env, 1)
        self.discoResource = simpy.Resource(env, 1)

    def quantDatagrams(self, mensagem):
        return mensagem / self.mss

    def overhead(self, mensagem):
        return self.quantDatagrams(mensagem) * (self.ovhdTCP + self.ovhdIP + self.ovhdFrame)

    def tempoRede(self, mensagem, largura):
        return 8 * (mensagem + self.overhead(mensagem)) / (1000000 * largura)

    def requestLan(self):
        yield self.env.timeout(self.tempoRede(self.reqHttpMedia, self.larguraBandaLan))

    def cpuHit(self):
        yield self.env.timeout(self.tempoAcertoCPU)

    def cpuMiss(self):
        yield self.env.timeout(self.tempoFaltaCPU)

    def disco(self, tamDoc):
        yield self.env.timeout(self.tempoDisco * tamDoc/1000)

    def requestRouter(self):
        yield self.env.timeout(self.latenciaRoteador / 1000000)

    def linkOutput(self):
        yield self.env.timeout(self.tempoRede(self.reqHttpMedia, self.larguraBandaLink) + 3 * self.tempoRede(0.0001, self.larguraBandaLink))

    def isp(self, tamDoc):
        yield self.env.timeout((2 * self.rtt / 1000) + (tamDoc / self.taxaDadosInternet))

    def linkInput(self, tamDoc):
        yield self.env.timeout(self.tempoRede(tamDoc, self.larguraBandaLink) + 2 * self.tempoRede(0.0001, self.larguraBandaLink))

    def responseRouter(self, tamDoc):
        yield self.env.timeout( (self.quantDatagrams(1204 * tamDoc) + 6) * self.latenciaRoteador * 0.000001)

    def responseLan(self, tamDoc):
        yield self.env.timeout(self.tempoRede(1024 * tamDoc, self.larguraBandaLan))
