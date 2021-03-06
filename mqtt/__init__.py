
"""
biblioteca para facilitar o uso da bilioteca mqtt 'paho'
"""

# exporta o caminho da bilioteca para o python PATH
import os, sys
basepath = os.path.split(__file__)[0]
dirpath  = os.path.split(basepath)[0]

if dirpath in sys.path:
    sys.path.remove(dirpath)

sys.path.insert(0, dirpath)

# pasta que contem o programa
PROGRAM_PATH = dirpath

# limpeza
del os, sys
del basepath
del dirpath

# modulos da blibioteca disponives por padrao
from mqtt import client, serial

# configura o que eh visivel fora da bilioteca
__all__ = ["cliente", "serial"] + client.__all__ + serial.__all__
