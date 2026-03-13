"""
Carregador de variáveis de ambiente por branch/ambiente.
Cada branch (dev/stage/prod) tem seu próprio config/.env isolado via git merge=ours.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env que está na mesma pasta (config/)
load_dotenv(Path(__file__).parent / '.env')
