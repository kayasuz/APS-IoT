
# ---------- preambulo ----------

# modulos necessarios
from mqtt.client import MQTTClient
from mqtt.serial import SerialHandler

# ------------ corpo ------------

broker = "localhost"

def on_message(client, topico, mensagem):
    print(f"{topico}: {mensagem}")

def listar_portas():
    import PySerial.tools.list_ports
    return list(serial.tools.list_ports.comports())

def selecionar_porta_serial(prompt=True):
    portas = listar_portas()
    if len(portas) == 0:
        print("erro: o arduino nao pode ser encontrado (ele esta conectado?)", file=sys.stderr)
        exit(1)

    # tenta encontrar um unico arduino para se conectar
    arduino = None
    for porta in portas:
        if porta.manufacturer is not None and porta.startswith("Arduino"):
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

def main():
    import sys
    try:
        client = MQTTClient(broker)
    except ConnectionRefusedError:
        print(f"falha ao conectar ao broker: conexao recusada", file=sys.stderr)
        exit(1)

    try:
        porta = selecionar_porta_serial()
    except ImportError:
        print("erro: PySerial nao esta instalado", file=sys.stderr)
        exit(1)
    
    if porta is None:
        exit(1)

    handler = SerialHandler(client, porta)
    client.message_callback(on_message)

    handler.encaminhar("temperature", "/dev/sensor/temp:0")
    handler.encaminhar("humidity",    "/dev/sensor/humi:0")

    client.subscribe("/dev/sensor/temp:0")
    client.subscribe("/dev/sensor/humi:0")

    client.loop_start()
    try:
        handler.loop_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
else:
    import sys
    print("erro: esse script nao deve ser importado", file=sys.stderr)
    exit(1)
