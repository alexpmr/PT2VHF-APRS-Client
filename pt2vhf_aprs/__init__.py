__version__ = "1.14.21"
APP_TOCALL = "APZVHF"

# v1.14.21: instala o modelo de topologia RF espaço-temporal após as
# constantes do pacote estarem disponíveis para database.py.
from . import spacetime_topology as _spacetime_topology

_spacetime_topology.install()
