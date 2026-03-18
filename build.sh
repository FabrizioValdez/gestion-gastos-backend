#!/usr/bin/env bash
# Build script para Render

# Instalar dependencias
pip install -r requirements.txt

# Recoger archivos estáticos
python manage.py collectstatic --noinput

# Aplicar migraciones
python manage.py migrate
