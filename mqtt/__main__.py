
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
    print(f"{topico}: {mensagem}")

def listar_portas():
    import serial.tools.list_ports
    return list(serial.tools.list_ports.comports())

def selecionar_porta_serial(prompt=True):
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
    import mqtt
    path = os.path.join(mqtt.PROGRAM_PATH, "config", "mqtt.json")
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

    cfg = carregar_arquivo_de_configuracao()

    broker = cfg.get("broker", None)
    if broker is None:
        print("falha ao carregas as configuracoes, campo 'broker' nao definido", file=sys.stderr)
        return
    if not isinstance(broker, str):
        print("falha ao carregar as configuracoes, campo 'broker' invalido", file=sys.stderr)
        return

    sensores = cfg.get("sensores", {})
    if not isinstance(sensores, dict):
        print("falha ao carregar as configuracoes, campo 'sensores' invalido", file=sys.stderr)
    else:
        sensores_ = carregar_configuracao_dos_sensores(sensores.items())
        if sensores_ is None:
            print("falha ao carregar as configuracoes devido ao erro acima", file=sys.stderr)
        else:
            print("configuracao carregada")
            return (broker, sensores_)

def carregar_configuracao_dos_sensores(sensores):

    carregados = []
    for nome_hardware, sensor in sensores:
        if not isinstance(sensor, dict):
            print(f"falha ao carregar a configuracao do sensor " 
                f"'{nome_hardware}', configuracao invalida", file=sys.stderr)
            return

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

    return carregados

def main():
    configuracao = carregar_configuracao()
    if configuracao is None:
        exit(1)

    broker, sensores = configuracao
    try:
        client = MQTTClient(broker)
    except ConnectionRefusedError:
        print(f"falha ao conectar ao broker '{broker}', conexao recusada", file=sys.stderr)
        exit(1)

    try:
        porta = selecionar_porta_serial()
    except ImportError as error:
        traceback.printexc()
        print("erro: PySerial nao esta instalado", file=sys.stderr)
        exit(1)

    if porta is None:
        exit(1)

    handler = SerialHandler(client, porta)
    client.message_callback(on_message)

    print("\nconfigurando handler de sensores...")
    for nome_hardware, nome, topico, *ignorado in sensores:
        handler.encaminhar(nome_hardware, topico)
        client.subscribe(topico)
        print(f"saida do sensor '{nome}' encaminhada para o topico '{topico}'")

    client.loop_start()
    print("\ncliente iniciado")
    try:
        handler.loop_forever()
    except KeyboardInterrupt:
        print("\nparando cliente")

if __name__ == "__main__":
    main()
else:
    import sys
    print("erro: esse script nao deve ser importado", file=sys.stderr)
    exit(1)
