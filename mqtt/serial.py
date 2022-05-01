
__all__ = []
def exportado(coisa):
    global __all__
    __all__.append(coisa.__name__)
    return coisa

@exportado
class SerialConnectionError(ConnectionError):
    pass

@exportado
class SerialHandler:

    def __init__(self, client, porta, baudrate=9600, codificacao=None):
        from mqtt.client import MQTTClient

        # checagem de tipo
        if not isinstance(client, MQTTClient):
            raise TypeError(
                f"expected {MQTTClient.__qualname__} for 'client', got {type(client).__qualname__}"
            )
        if not isinstance(porta, str):
            raise TypeError(f"expected str for 'porta', got {type(porta).__qualname__}")
        if not isinstance(baudrate, int):
            raise TypeError(f"expected int for 'baudrate', got {type(baudrate).__qualname__}")
        if codificacao is None:
            codificacao = "ascii"
        elif not isinstance(codificacao, str):
            raise TypeError(f"expected None or str for 'codificacao', got {type(codificacao).__qualname__}")

        # checagem de valor
        if baudrate <= 0:
            raise ValueError(f"'baudrate' should be a positive non-zero integer")

        # conexao com o dispositivo
        try:
            import serial
        except ImportError as error:
            class_name = self.__class__.__qualname__
            raise ValueError(f"can't create {class_name} handler, PySerial not installed") from error
        try:
            dispositivo = serial.Serial(porta, baudrate)
        except seria.serialutil.SerialException as error:
            raise SerialConnectionError from error

        self._codificacao    = codificacao
        self._dispositivo    = dispositivo
        self._client         = client
        self._topicos        = {}
        self._topico_erros   = None
        self._callback_erros = None

    def encaminhar(self, sensor, topico):
        if topico is None:
            try:
                del self._topicos[sensor]
            except KeyError:
                pass
        else:
            self._topicos[sensor] = topico

    def encaminhar_erros(self, topico):
        if topico is None or isinstance(topico, str):
            self._topico_erros = topico
        else:
            raise TypeError(f"expected None or str for 'topico', got {type(topico).__qualname__}")

    def gerenciar_erros(self, callback):
        if callback is None or callable(callback):
            self._callback_erros = callback
        else:
            raise TypeError(f"expected None or callable for 'callback', got {type(callback).__qualname__}")

    def loop_forever(self):
        dispositivo = self._dispositivo
        codificacao = self._codificacao
        newline = '\n'.encode(codificacao)
        while True:
            mensagem = dispositivo.read_until(newline)
            if isinstance(mensagem, bytes):
                # NOTE: serial.Serial.read_until() retorna bytes a partir da versao 2.5
                try:
                    mensagem = mensagem.decode(codificacao)
                except UnicodeDecodeError:
                    # assume dados invalidos
                    continue

            if mensagem.endswith('\r\n'):
                mensagem = mensagem[:-2]
            elif mensagem.endswith('\n'):
                mensagem = mensagem[:-1]

            if mensagem.startswith("error"):
                self._processar_erro(mensagem)            
            else:
                try:
                    categoria, sensor, valor = mensagem.split(' ', 2)
                except ValueError:
                    # mensagem invalida, ignore
                    continue

                if categoria == "sensor":
                    self._processar_sensor(sensor, valor)

    def _processar_erro(self, mensagem):
        if callable(self._callback):
            self._callback(mensagem)
        if self._topico_erros is not None:
            self._client.publish(self._topico_erros, mensagem)

    def _processar_sensor(self, sensor, valor):
        topico = self._topicos.get(sensor)
        if topico is not None:
            self._client.publish(topico, valor)

# limpeza
del exportado
