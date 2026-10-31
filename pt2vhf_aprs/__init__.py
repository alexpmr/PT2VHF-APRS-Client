__version__ = "1.15.5"
APP_TOCALL = "APZVHF"

# A topologia RF espaço-temporal (spacetime_topology.py) é ligada
# explicitamente ao final de database.py; importar database aqui garante a
# ordem correta de inicialização dos dois módulos.
from . import database as _database  # noqa: E402,F401
