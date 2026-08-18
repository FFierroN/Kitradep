# Guia de despliegue - Bot KitraDep

Esta guia cubre el despliegue del bot hibrido en un VPS para produccion.
Asume Ubuntu 24.04. Adaptable a cualquier Linux.

> Para desarrollo local ver README.md. Esta guia es para el servidor 24/7.

---

## 0. Antes de empezar (checklist)

- [ ] VPS contratado (Hetzner CX22 / CAX11, Vultr Santiago, etc.)
- [ ] Dominio apuntando al IP del VPS (registro A)
- [ ] API key de Gemini
- [ ] Acceso SSH al VPS
- [ ] (Opcional) cuenta Backblaze B2 para backups
- [ ] (Opcional) SMTP para notificaciones al staff

---

## 1. Preparar el servidor

```bash
# Conectarse
ssh root@TU_IP

# Actualizar
apt update && apt upgrade -y

# Instalar Docker (forma oficial y simple)
curl -fsSL https://get.docker.com | sh

# Verificar
docker --version
docker compose version
```

---

## 2. Traer el codigo

```bash
# Clonar el repo (o subirlo por scp)
git clone https://github.com/TUUSUARIO/chatbot-kitradep.git
cd chatbot-kitradep
```

---

## 3. Configurar variables

```bash
cp .env.example .env
nano .env
```

Como minimo para produccion:

```
LLM_BACKEND=gemini
GEMINI_API_KEY=tu_key_real
HOST=0.0.0.0
PUERTO=8765
ABRIR_NAVEGADOR=0
HANDOFF_CONTACTO=+56 9 XXXX XXXX
```

---

## 4. Levantar con Docker

```bash
docker compose up -d          # build + arranque en segundo plano
docker compose logs -f        # ver logs en vivo (Ctrl+C para salir)
docker compose ps             # estado
```

Probar localmente en el server:

```bash
curl http://127.0.0.1:8765/health
# {"status":"ok","backend_llm":"GeminiLLM","sesiones":0}
```

---

## 5. Reverse proxy + HTTPS con Caddy

Caddy saca certificado SSL automatico (Let's Encrypt), sin configuracion.

```bash
# Instalar Caddy
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
  gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
  tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy
```

Editar `/etc/caddy/Caddyfile`:

```
kitradep.tudominio.cl {
    reverse_proxy 127.0.0.1:8765
}
```

```bash
systemctl reload caddy
```

Listo: `https://kitradep.tudominio.cl` ya tiene SSL valido y apunta al bot.
Esta es la URL que se configura como webhook en Meta/Twilio (Fase 4).

---

## 6. Backups automaticos

```bash
# Probar backup manual
docker compose exec bot python scripts/backup.py

# Programar en cron (todos los dias 3 AM)
crontab -e
# Agregar:
0 3 * * * cd /root/chatbot-kitradep && docker compose exec -T bot python scripts/backup.py >> /var/log/kitradep_backup.log 2>&1
```

Para subir a Backblaze B2, completar las variables B2_* en `.env` e instalar
boto3 (agregarlo a requirements.txt o `pip install boto3` en el contenedor).

---

## 7. Monitoreo (UptimeRobot)

1. Crear cuenta en https://uptimerobot.com (gratis)
2. Add New Monitor -> HTTP(s)
3. URL: `https://kitradep.tudominio.cl/health`
4. Interval: 5 min
5. Configurar alerta por email

---

## 8. Actualizar el bot (deploy de cambios)

```bash
cd /root/chatbot-kitradep
git pull
docker compose up -d --build     # reconstruye y reinicia
```

Rollback si algo sale mal:

```bash
git log --oneline          # ver commits
git checkout COMMIT_ANTERIOR
docker compose up -d --build
```

---

## 9. Comandos utiles

```bash
docker compose restart          # reiniciar el bot
docker compose down             # detener
docker compose logs --tail=100  # ultimas 100 lineas de log
docker stats kitradep-bot       # uso de CPU/RAM en vivo
```

---

## 10. Checklist post-deploy

- [ ] `curl https://kitradep.tudominio.cl/health` responde ok
- [ ] SSL valido (candado verde en el navegador)
- [ ] UptimeRobot monitoreando
- [ ] Backup manual probado
- [ ] Cron de backup configurado
- [ ] LLM_BACKEND=gemini y responde de verdad
- [ ] Notificaciones al staff llegan (probar handoff)
