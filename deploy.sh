#!/bin/bash

# === CONFIGURAÇÕES ===
USER="root"
SERVER="31.97.162.80"
PROJECT_DIR="/opt/portal"
VENV_DIR="/opt/portal/venv"

echo "📦 Enviando arquivos para o servidor..."
rsync -avz --exclude 'venv' --exclude '.git' --exclude '__pycache__' ./ $USER@$SERVER:$PROJECT_DIR/

echo "🔗 Conectando no servidor..."
ssh $USER@$SERVER << EOF
  echo "📁 Ativando virtualenv"
  source $VENV_DIR/bin/activate

  echo "🧹 Coletando arquivos estáticos"
  python $PROJECT_DIR/manage.py collectstatic --noinput

  echo "🔁 Reiniciando Gunicorn"
  pkill gunicorn
  gunicorn repasse_project.wsgi:application --bind 127.0.0.1:8000 --daemon

  echo "✅ Deploy concluído no servidor!"
EOF