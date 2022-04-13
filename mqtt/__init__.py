
# exporta o caminho da bilioteca para o python PATH
import os, sys
basepath = os.path.split(__file__)[0]
dirpath  = os.path.split(basepath)[0]

if dirpath in sys.path:
	sys.path.remove(dirpath)

sys.path.insert(0, dirpath)

# limpeza
del os, sys
del basepath
del dirpath

# modulos da blibioteca disponives por padrao
from mqtt import client

# configura o que eh visivel fora da bilioteca
__all__ = ["cliente"] + client.__all__
