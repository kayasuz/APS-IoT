
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
		self.on_connect = None
		self.on_message = None
		self._broker    = broker
		self._porta     = porta

		# conecta o cliente com o broker
		import functools
		self._handler = mqtt_client.Client(f"python-{self._id:04X}")
		self._handler.on_connect = self._handle_connect
		self._handler.on_message = self._handle_message
		self._handler.connect(broker, porta)

		# registra a instancia
		if self.clientes.setdefault(self._id, self) is not self:
			#TODO: mudar o tipo de excecao
			class_name = self.__class__.__qualname__
			raise Exception(f"can't register {class_name} with id 0x{id_:04X}, id already in use")

	def __repr__(self):
		class_name = self.__class__.__qualname__
		return f"{class_name}(id=0x{self._id:04X})"

	@classmethod
	def gerar_id_cliente(cls):
		clientes = cls.clientes
		ID_MAX   = cls.ID_CLIENTE_MAXIMO
		while True:
			id_ = random.randint(0, ID_MAX)
			if id_ not in clientes:
				return id_


	# ====== handlers internos =======

	def _handle_message(self, handler, userdata, message):
		if self.on_message is not None:
			self.on_message(handler, message.topic, message.payload.decode())

	def _handle_connect(self, handler, userdata, flags, rc):
		if rc == 0:
			print(f"cliente MQTT 0x{self._id:04X} conectado ao broker '{self._broker}' na porta '{self._porta}'")
		else:
			print(f"cliente MQTT 0x{self._id:04X} falhou em conectar ao broker com codigo de erro {rc}", file=sys.stderr)

		if self.on_connect is not None:
			self.on_connect(handler, userdata, flags, rc)


	# ====== funcoes principais ======

	def subscribe(self, topico):
		return self._handler.subscribe(topico)

	def publish(self, topico, mensagem):
		return self._handler.publish(topico, mensagem)

	def loop_start(self):
		self._handler.loop_start()

	def loop_forever(self):
		self._handler.loop_forever()

	# ====== setters e getters =======

	def connect_callback(self, *callback):
		if len(callback) == 0:
			return self.on_connect
		elif len(callback) == 1:
			self.on_connect = callback[0]
			return self.on_connect
		else:
			raise TypeError(f"{__func__} expected from 1 to 2 arguments, got {len(callback)}")

	def message_callback(self, *callback):
		if len(callback) == 0:
			return self.on_message
		elif len(callback) == 1:
			self.on_message = callback[0]
			return self.on_message
		else:
			raise TypeError(f"{__func__} expected from 1 to 2 arguments, got {len(callback)}")


# limpeza
del exportado
