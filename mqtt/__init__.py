
# exporta o caminho da bilioteca para o python PATH
import os, sys
basepath = os.path.split(__file__)[0]
sys.path.insert(0, basepath)

# limpeza
del os, sys
del basepath

# modulos da blibioteca disponives por padrao
from mqtt import cliente

# configura o que eh visivel fora da bilioteca
__all__ = ["cliente"] + cliente.__all__
