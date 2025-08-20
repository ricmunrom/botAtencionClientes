#!/usr/bin/env python3
"""
WSGI config for Kavak Bot
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Importar la aplicación Flask
from app import app

# Para debugging en desarrollo
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)