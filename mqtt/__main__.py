
# certifique-se que a biblioteca seja carregada corretamente
import __init__; del __init__

# modulos necessarios
from mqtt.client import MQTTClient

def main():
	pass

if __name__ == "__main__":
	main()
else:
	import sys
	print("erro: esse script nao deve ser importado", file=sys.stderr)
	exit(1)
