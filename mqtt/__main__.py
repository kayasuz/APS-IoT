
# ---------- preambulo ----------

# modulos necessarios
from mqtt.client import MQTTClient
from mqtt.serial import SerialHandler

# ------------ corpo ------------

broker = "localhost"

def on_message(client, topico, mensagem):
    print(f"{topico}: {mensagem}")

def main():
    import sys
    try:
        client = MQTTClient(broker)
    except ConnectionRefusedError:
        print(f"falha ao conectar ao broker: conexao recusada", file=sys.stderr)
        exit(1)

    if sys.platform == "linux":
        porta = "/dev/ttyACM0"
    elif sys.platform.lower().startswith("windows"):
        porta = "COM5"
    else:
        print(f"plataforma nao suportada")
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
