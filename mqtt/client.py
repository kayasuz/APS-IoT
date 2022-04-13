
"""
modulo com classes de supporte para facilitar
a criacao de clientes MQTT
"""

# ---------- preambulo ----------

# modulos do sistema usados
import sys

# tenta importar o paho (modulo de cliente MQTT)
try:
	from paho.mqtt import client as mqtt_client
except ImportError:
	print("error: paho is not installed, please install paho for python3")
	exit(1)

# modulos necessarios
import random


# ----- funcoes auxiliares -----

__all__ = []
def exportado(coisa):
	"""
	decorador para adicionar nomes que devem
	ser visiveis fora do modulo ao __all__.
	"""

	global __all__
	__all__.append(coisa.__name__)
	return coisa


# ---------- classes ----------

@exportado
class MQTTClient:

	"""
	classe de suporte para facilitar a criacao de clientes MQTT
	"""

	# porta padrao MQTT
	PORTA_MQTT_PADRAO = 1883

	# id maximo de cliente (32 bits)
	ID_CLIENTE_MAXIMO = (2 << 16) - 1

	# clientes ativos
	clientes = {}

	def __init__(self, broker, porta=None):
		if porta is None:
			porta = self.PORTA_MQTT_PADRAO

		# checagem dos argumentos
		if not isinstance(broker, str):
			raise TypeError(f"expected str for 'broker', got {type(broker).__qualname__}")
		if not isinstance(porta, int):
			raise TypeError(f"expected int for 'porta', got {type(porta).__qualname__}")
		if porta <= 0:
			raise TypeError(f"expected a non-zero positive value for 'porta', got {porta}")

		# gera um id de cliente valido
		self._id = self.gerar_id_cliente()

		# seta os atributos
		self._broker    = broker
		self._porta     = porta

		# conecta o cliente com o broker
		self._handler = mqtt_client.Client(f"python-{self._id:04X}")
		self._handler.on_connect = self.on_connect
		self._handler.connect(broker, porta)

		# registra a instancia
		if self.clientes.setdefault(self._id, self) is not self:
			#TODO: mudar o tipo de excecao
			class_name = self.__class__.__qualname__
			raise Exception(f"can't register {class_name} with id 0x{id_:04X}, id already in use")

	@classmethod
	def gerar_id_cliente(cls):
		clientes = cls.clientes
		ID_MAX   = cls.ID_CLIENTE_MAXIMO
		while True:
			id_ = random.randint(0, ID_MAX)
			if id_ not in clientes:
				return id_

	@classmethod
	def on_connect(cls, cliente, userdata, flags, rc):
		if rc:
			print(f"{cls.__name__}: failed to connect with error code {rc}", file=sys.stderr)

	# ====== funcoes principais ======

	def subscribe(self, topico):
		return self._handler.subscribe(topico)

	def publish(self, topico, mensagem):
		return self._handler.publish(topic, mensagem)

	def loop_start(self):
		self._handler.loop_start()

	def loop_forever(self):
		self._handler.loop_forever()


# limpeza
del exportado
