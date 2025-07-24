# === CONFIGURAÇÕES ===
$User = "root"
$Server = "31.97.162.80"
$RemotePath = "/opt/portal"
$VenvPath = "/opt/portal/venv"
$ProjectPath = Get-Location
$ZipPath = Join-Path $ProjectPath "deploy.zip"

Set-Location -Path $ProjectPath

Write-Host " Enviando arquivos para o servidor via SCP..."

# === EXCLUSÃO TEMPORÁRIA DO BANCO LOCAL ===
if (Test-Path "$ProjectPath\db.sqlite3") {
    Rename-Item "$ProjectPath\db.sqlite3" "db.sqlite3.ignore"
}

# === Compactação correta mantendo estrutura ===
Write-Host " Compactando arquivos preservando estrutura..."

$exclude = @("venv", "__pycache__", ".git", "db.sqlite3", "deploy.zip")

if (Test-Path "deploy.zip") { Remove-Item "deploy.zip" }

# Cria uma lista de arquivos válidos preservando estrutura relativa
$filesToInclude = Get-ChildItem -Path $ProjectPath -Recurse -File | Where-Object {
    $relativePath = $_.FullName.Substring($ProjectPath.Length + 1)
    ($exclude -notcontains $_.Name) -and ($exclude -notcontains $relativePath.Split('\')[0])
}
Compress-Archive -Path "$ProjectPath\*" -DestinationPath $ZipPath -Force

# Restaura banco local após zip
if (Test-Path "$ProjectPath\db.sqlite3.ignore") {
    Rename-Item "db.sqlite3.ignore" "db.sqlite3"
}

# === Envia para o servidor ===
scp $ZipPath "${User}@${Server}:${RemotePath}"

# === SSH remoto ===
Write-Host " Conectando ao servidor para descompactar, fazer backup e reiniciar..."

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

ssh $User@$Server @"
  set -e
  cd $RemotePath

  echo ' Fazendo backup do banco atual...'
  if [ -f db.sqlite3 ]; then
    cp db.sqlite3 db.sqlite3.backup_$timestamp
  fi

  echo ' Descompactando arquivos...'
  unzip -o deploy.zip -d temp_deploy
  cp -r temp_deploy/* .
  rm -rf temp_deploy
  rm deploy.zip

  echo ' Corrigindo permissões...'
  chmod 755 $RemotePath
  find $RemotePath/staticfiles -type d -exec chmod 755 {} \;
  find $RemotePath/staticfiles -type f -exec chmod 644 {} \;
  chown -R www-data:www-data $RemotePath/staticfiles

  echo ' Ativando ambiente virtual...'
  source $VenvPath/bin/activate

  echo ' Coletando arquivos estáticos...'
  python manage.py collectstatic --noinput

  echo ' Aplicando migrações...'
  python manage.py migrate

  echo ' Reiniciando Gunicorn...'
  pkill gunicorn || true
  gunicorn repasse_project.wsgi:application --bind 127.0.0.1:8000 --daemon

  echo ' Deploy finalizado com sucesso.'
"@

Write-Host "✅ Deploy concluído com sucesso!"