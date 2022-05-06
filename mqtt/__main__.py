
# ---------- preambulo ----------

# modulos necessarios
from mqtt.client import MQTTClient
from mqtt.serial import SerialHandler

# modulos da biblioteca padrao
import os
import sys
import traceback
import json

# ------------ corpo ------------

def on_message(client, topico, mensagem):
    """
    depuracao das mensagens recebidas pelo cliente MQTT
    """
    print(f"{topico}: {mensagem}")

def listar_portas():
    """
    funcao auxiliar para listagem de portas seriais
    """
    import serial.tools.list_ports
    return list(serial.tools.list_ports.comports())

def selecionar_porta_serial(prompt=True):
    """
    descobre a porta serial conectada ao Arduino automaticamente,
    e em caso de falha pode perguntar ao usuario qual porta usar se
    prompt for um valor verdadeiro (ou seja, bool(prompt) == True)

    internamente essa funcao procura por portas seriais (geralmente USB)
    conectadas a um dispositivo cujo nome do fabricante comeca com "Arduino",
    caso mais de um dispositivo seja encontrado um menu aparecera com a lista
    de todas a portas seriais conhecidas se a opcao 'prompt' for verdade (padrao),

    por conta disso placas podem ser ignoradas caso o fabricante nao possa ser
    identificado, o que pode levar a selecao da unica placa com fabricante conhecido

    se 'prompt' for falso nada sera retornado caso varias portas sejam encontradas
    """
    portas = listar_portas()
    if len(portas) == 0:
        print("erro: o arduino nao pode ser encontrado (ele esta conectado?)", file=sys.stderr)
        exit(1)

    # tenta encontrar um unico arduino para se conectar
    arduino = None
    for porta in portas:
        manufacturer = porta.manufacturer
        if manufacturer is not None and manufacturer.startswith("Arduino"):
            if arduino is not None:
                # mais de um arduino encontrado
                break

            arduino = porta.device
    else:
        # possivel arduino encontrado (nao mais do que um)
        if arduino is not None:
            return arduino

    # verifica se pode usar o prompt (falso se usado por scripts)
    if not prompt:
        return

    # selecao do arduino pelo usuario
    import math
    digitos = math.floor(math.log10(len(portas))) + 1
    try:
        while True:
            for n, porta in enumerate(portas):
                print(f" {n:>{digitos}}: {porta.device}")

            resp = input("Numero da porta (ou q para cancelar): ")
            if resp.strip(' ').lower() == 'q':
                break

            try:
                idx = int(resp) 
                return portas[idx].device
            except (ValueError, IndexError):
                pass

    except KeyboardInterrupt:
        print()

def carregar_arquivo_de_configuracao():
    """
    carrega o arquivo de configuracao sem processa-lo,
    retorna None em caso de falha de leitura ou decodificacao
    e imprime uma mensagem de erro

    o arquivo deve estar localizado em uma pasta chamada 'config'
    na mesma pasta em que se encontra essa biblioteca e deve ser
    nomeado de 'mqtt.json' para ser carregado
    """

    # resolucao do caminho do arquivo
    import mqtt
    path = os.path.join(mqtt.PROGRAM_PATH, "config", "mqtt.json")

    # leitura e decodificacao do arquivo
    try:
        with open(path, 'r') as fh:
            return json.load(fh)
    except FileNotFoundError as error:
        print("falha ao carregar as configuracoes, "
            f"arquivo de configuracao nao encontrado: {path}")
    except (json.JSONDecodeError, OSError) as error:
        print(f"{traceback.formatexc()}"
            "\nfalha ao carregar as configuracoes devido ao erro acima\n", file=sys.stderr)

def carregar_configuracao():
    """
    carrega o arquivo de configuracao processando os parametros,
    retorna None em caso de falha de leitura, de decodificacao
    ou se alguma opcao for invalida e imprime uma mensagem de erro
    """

    # carregamento da configuracao bruta (sem processamento)
    cfg = carregar_arquivo_de_configuracao()

    # processa a URL do broker
    broker = cfg.get("broker", None)
    if broker is None:
        print("falha ao carregas as configuracoes, campo 'broker' nao definido", file=sys.stderr)
        return
    if not isinstance(broker, str):
        print("falha ao carregar as configuracoes, campo 'broker' invalido", file=sys.stderr)
        return

    # processa a lista de sensores e retorna
    sensores = cfg.get("sensores", {})
    if not isinstance(sensores, dict):
        print("falha ao carregar as configuracoes, campo 'sensores' invalido", file=sys.stderr)
    else:
        sensores_ = carregar_configuracao_dos_sensores(sensores.items())
        if sensores_ is None:
            print("falha ao carregar as configuracoes devido ao erro acima", file=sys.stderr)
        else:
            # retorna a configuracao processada
            print("configuracao carregada")
            return (broker, sensores_)

def carregar_configuracao_dos_sensores(sensores):
    """
    processamento da definicao de sensores na configuracao,
    ACEITANDO ENTRADAS DUPLICADAS

    processa uma lista de pares com o nome de hardware do sensor
    e a configuracao do sensor em uma lista de tuplas contendo o 
    nome de hardware, nome comum e topico de cada sensor
    """

    carregados = []
    for nome_hardware, sensor in sensores:
        # checagem de tipo
        if not isinstance(sensor, dict):
            print(f"falha ao carregar a configuracao do sensor " 
                f"'{nome_hardware}', configuracao invalida", file=sys.stderr)
            return

        # checagem dos campos
        campos = []
        for campo in ("nome", "topico"):
            if campo in sensor:
                valor = sensor[campo]
                if isinstance(valor, str) and len(valor) > 0:
                    campos.append(valor)
                    continue
    
            print(f"falha ao carregar a configuracao do sensor "
                f"'{nome_hardware}', campo '{campo}' nao definido")
            return

        carregados.append((nome_hardware, *campos))

    # retorno dos sensores processados
    return carregados

def main():
    """
    funcao principal
    
    carrega a configuracao, cliente MQTT, handler de sensores,
    topicos de cada sensor associado e inicia o servico MQTT
    ate que ctrl-c seja pressionado (ou o equivalente que gere
    KeyboardInterrupt)

    enquanto o handler estiver ativo, leituras dos sensores
    sao encaminhadas a seus topicos definidos na configuracao
    """

    # leitura da configuracao
    configuracao = carregar_configuracao()
    if configuracao is None:
        exit(1)

    broker, sensores = configuracao

    # conexao com o broker
    try:
        client = MQTTClient(broker)
    except ConnectionRefusedError:
        print(f"falha ao conectar ao broker '{broker}', conexao recusada", file=sys.stderr)
        exit(1)

    # deteccao da porta serial conectada ao arduino
    try:
        porta = selecionar_porta_serial()
    except ImportError as error:
        traceback.printexc()
        print("erro: PySerial nao esta instalado", file=sys.stderr)
        exit(1)

    if porta is None:
        exit(1)

    # instanciacao do handler de sensores e configuracao
    # do callback de depuracao de mensagens do cliente MQTT
    handler = SerialHandler(client, porta)
    client.message_callback(on_message)

    # associacao dos topicos de cada sensor
    print("\nconfigurando handler de sensores...")
    for nome_hardware, nome, topico, *ignorado in sensores:
        handler.encaminhar(nome_hardware, topico)
        client.subscribe(topico)
        print(f"saida do sensor '{nome}' encaminhada para o topico '{topico}'")

    # inicia o servicos do cliente MQTT e handler de sensores
    client.loop_start()
    print("\ncliente iniciado")
    try:
        handler.loop_forever()
    except KeyboardInterrupt:
        print("\nparando cliente")

# executa a funcao principal caso esse modulo seja executado
# e evita que ele seja importado por outros scripts
if __name__ == "__main__":
    main()
else:
    import sys
    print("erro: esse script nao deve ser importado", file=sys.stderr)
    exit(1)
