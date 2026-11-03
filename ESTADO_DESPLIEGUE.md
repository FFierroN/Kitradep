# Estado del despliegue - KitraDep

> Ultima actualizacion: 2026-11-02.
> Bitacora de todo lo que se hizo para sacar el bot del PC y ponerlo en un
> servidor 24/7, mas el estado de WhatsApp/Meta y lo que falta.
> Complementa a `GUIA_PARA_RETOMAR.md` (el plan) y `DEPLOY.md` (comandos genericos).
>
> NUNCA escribir aqui claves, tokens ni contrasenas: el repo es PUBLICO.
> Los secretos viven solo en el `.env` del PC y en el `.env` del servidor.

---

## 1. Resumen en una linea

El bot corre 24/7 en AWS con Gemini y HTTPS. Falta el webhook de WhatsApp
(codigo) y un canal de WhatsApp habilitado: Meta exige verificar el negocio,
asi que la demo se hara con Twilio Sandbox.

---

## 2. Servidor (AWS EC2)

| Item | Valor |
|---|---|
| Proveedor | AWS, cuenta con **Free plan** (sin cobros; dura 6 meses o hasta agotar los creditos) |
| Region | **us-east-2 (Ohio)** |
| Instancia | `kitradep-bot`, tipo **t3.micro** (2 vCPU, 1 GB RAM) |
| Sistema | Ubuntu Server 24.04 LTS (amd64) |
| Disco | 20 GB gp3 |
| Swap | 1 GB (`/swapfile`, persistente en `/etc/fstab`) |
| IP publica | **3.20.141.102** (IP elastica: fija, no cambia al reiniciar) |
| URL publica | **https://3-20-141-102.sslip.io** |
| Grupo de seguridad | Entrada: SSH (22) solo desde la IP de Felipe, HTTP (80) y HTTPS (443) abiertos |

### Por que AWS y no otra opcion
- **DreamHost**: el plan actual es hosting compartido; un VPS es pago aparte.
- **Oracle Cloud Always Free**: registro muy lento, se descarto.
- **Google Cloud e2-micro**: valido, quedo como alternativa.
- **AWS Free plan**: VPS real, sin cobros mientras dure el plan. Al terminar,
  AWS **cierra la cuenta** (no cobra); hay 90 dias para pasar a plan pagado.

### Como entrar al servidor
Desde PowerShell en el PC, en la carpeta donde esta la llave `kitradep.pem`:

```powershell
ssh -i kitradep.pem ubuntu@3.20.141.102
```

- La llave `.pem` se descargo al crear la instancia. Es privada: no se sube
  a git ni se comparte. Se le quito la herencia de permisos con
  `icacls kitradep.pem /inheritance:r /grant:r "$($env:USERNAME):R"`.
- "EC2 Instance Connect" (terminal en el navegador) NO funciona porque SSH
  solo acepta la IP de Felipe. Si cambia la IP de su casa, hay que actualizar
  la regla SSH del grupo de seguridad ("Mi IP").

### Lo que se instalo (en orden)
1. `sudo apt update && sudo apt upgrade -y`
2. Swap de 1 GB.
3. Docker: `curl -fsSL https://get.docker.com | sudo sh`
4. Repo: `git clone https://github.com/FFierroN/Kitradep.git` (queda en `~/Kitradep`).
5. `.env` en `~/Kitradep/.env` (ver seccion 3).
6. Bot: `sudo docker compose up -d --build` (contenedor `kitradep-bot`,
   `restart: unless-stopped`, base de datos en el volumen `kitradep_kitradep_data`).
7. Caddy (HTTPS automatico con Let's Encrypt) desde el repo oficial de Caddy.
8. IP elastica asociada a la instancia.

---

## 3. Configuracion del bot en el servidor (`.env`)

Variables cambiadas respecto a `.env.example` (sin valores secretos):

```
LLM_BACKEND=gemini
GEMINI_API_KEY=<la key de Gemini, la misma del PC>
GEMINI_MODEL=gemini-3.5-flash-lite
HOST=0.0.0.0
ABRIR_NAVEGADOR=0
```

Sobre el modelo:
- `gemini-3.5-flash` agoto su limite gratis (20 consultas/dia por modelo).
- `gemini-flash-latest` tardaba mas de 45 s y daba `DeadlineExceeded`.
- `gemini-3.5-flash-lite` responde en ~1-2 s. Es el que se usa hoy (PC y servidor).
- El plan gratis de Gemini **no alcanza para pacientes reales**: hay que
  activar facturacion antes del lanzamiento.

---

## 4. HTTPS y que queda expuesto (Caddy)

Archivo `/etc/caddy/Caddyfile` del servidor:

```
3-20-141-102.sslip.io {
	@permitido path /health /webhook /webhook/*
	handle @permitido {
		reverse_proxy 127.0.0.1:8765
	}
	handle {
		respond "No encontrado" 404
	}
}
```

- **sslip.io** es un servicio gratuito que convierte la IP en un nombre
  (`3-20-141-102.sslip.io` -> `3.20.141.102`). Asi Caddy puede sacar
  certificado HTTPS sin tocar el dominio de KitraDep.
- Desde internet **solo** se puede llegar a `/health` y `/webhook`. El
  simulador web queda privado (404) para que nadie gaste la cuota de Gemini.
- El puerto 8765 del bot NO esta abierto en el grupo de seguridad; solo
  Caddy (80/443) recibe trafico.

Verificado el 2026-11-02:

| Prueba | Resultado |
|---|---|
| `https://3-20-141-102.sslip.io/health` | 200, `{"status":"ok","backend_llm":"GeminiLLM"}` |
| `https://3-20-141-102.sslip.io/` | 404 (simulador bloqueado) |
| `http://...` | redirige a `https://` |

### Comandos utiles en el servidor

```bash
cd ~/Kitradep
curl http://127.0.0.1:8765/health          # bot vivo?
sudo docker compose logs --tail=100        # logs del bot
sudo docker compose restart                # reiniciar el bot
git pull && sudo docker compose up -d --build   # desplegar cambios del repo
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo journalctl -u caddy -n 30 --no-pager  # logs de Caddy / certificado
```

---

## 5. Dominio de KitraDep (para el subdominio definitivo)

- Dominio: **kinetraumadeportivo.com**.
- Esta **registrado en DreamHost**, pero sus nameservers son de
  **HostingPlus** (`dns1/dns2/dns3.hostingplus.cl`). La web apunta a
  `192.140.58.15` (HostingPlus).
- **No tocar los nameservers en DreamHost** ("Cambiar"): podria dejar caida
  la pagina web y el correo de la clinica.
- Agregar registros DNS en DreamHost no tiene efecto (el DNS real esta en
  HostingPlus).
- Para `bot.kinetraumadeportivo.com` hay que crear en **HostingPlus**
  (cPanel -> Editor de zona) un registro `A`: `bot` -> `3.20.141.102`.
  Despues se cambia el nombre en el Caddyfile.
- Tambien existe `kinetraumadeportivo.cl`, con DNS en otro proveedor
  (`domaincontrol.com`, GoDaddy). Pendiente de revisar.

---

## 6. WhatsApp / Meta

### Lo que se creo
- Cuenta de desarrollador en developers.facebook.com con el Facebook personal
  de Felipe (Meta no permite registrarse solo con correo).
- Portafolio comercial **"Kitradep"** y app **"Kitradep Bot"** (caso de uso
  "Conectarte con los clientes a traves de WhatsApp").
- Numero de prueba de Meta asignado (Phone number ID `1555420157644002`,
  WhatsApp Business Account ID `1159975483270127`). Estos IDs no son secretos.
- Al generar el token se eligio "Activar solo las cuentas de WhatsApp actuales".

### Bloqueo actual
Al enviar el mensaje de prueba, Meta respondio **error 131031 "Business
Account locked"**. En el resumen de la cuenta aparece:

> Cuenta restringida - "Before you can begin messaging, you will need to verify your business."
> Duracion: Permanente (hasta verificar el negocio).

O sea: **sin verificar el negocio, Meta no deja enviar mensajes, ni siquiera
desde el numero de prueba**. La verificacion requiere documentos legales de
KitraDep (RUT de empresa, documento oficial, direccion, sitio web), que debe
aportar el gerente.

### Decision para la demo
- Demo con **Twilio Sandbox**: solo pide correo y celular, sin verificacion
  ni tarjeta. El trial incluye ~100 mensajes de WhatsApp, maximo 50 por dia,
  y dura 30 dias. Crear la cuenta cerca de la fecha de la demo.
- Probar y ajustar el bot en el simulador local (gratis), y reservar Twilio
  para validar la conexion y para la demo.
- Lanzamiento oficial: **Meta Cloud API directo** (sin el recargo por mensaje
  de Twilio). La app y el portafolio de Meta quedan listos esperando la verificacion.
- **Descartado**: Evolution API en modo Baileys (no oficial, viola los
  terminos de WhatsApp, riesgo de que bloqueen el numero de la clinica).

### Traspaso al gerente
Todo vive en el portafolio "Kitradep", no en el Facebook de Felipe. Para
traspasarlo: agregar al gerente como administrador con control total del
portafolio y como administrador de la app; despues Felipe puede salir o
quedar como soporte. Las credenciales del bot viven en `.env`, asi que
cambiar de cuenta o de app no requiere tocar codigo.

---

## 7. Costos (estimacion, verificar antes de presentar)

- Hoy: **USD 0** (AWS Free plan, Gemini gratis, Twilio trial).
- Meta cobra por mensaje desde julio 2025. Hay reportes de que desde el
  **1 de octubre de 2026** tambien se cobran los mensajes de servicio
  (respuestas a pacientes) en Chile, ~CLP 15-22 c/u. **No confirmado en la
  pagina oficial de Meta**: revisarlo y actualizar `COSTOS.md`, que todavia
  dice que son gratis.
- Estimacion con ~300 pacientes/mes: ~USD 55-90/mes si se cobran los mensajes
  de servicio; ~USD 10-25/mes si siguen gratis (casi todo servidor + Gemini).

---

## 8. Lo que falta

### Para la demo al gerente
- [ ] **Webhook** (`whatsapp_webhook.py`): recibe mensajes, los pasa a
      `router.py` y responde. Disenarlo para Twilio ahora y Meta despues,
      con tests offline.
- [ ] Crear la cuenta de **Twilio**, activar el Sandbox y registrar
      `https://3-20-141-102.sslip.io/webhook`.
- [ ] Desplegar en el servidor (`git pull` + `docker compose up -d --build`)
      y probar desde el celular.

### Si el gerente aprueba
- [ ] Verificar el negocio en Meta con documentos de KitraDep.
- [ ] Decidir el numero definitivo: coexistencia con el WhatsApp Business
      actual, migrarlo a la API, o numero nuevo.
- [ ] Token permanente de Meta (usuario del sistema) y credenciales en el `.env` del servidor.
- [ ] Agregar al gerente como administrador del portafolio y de la app.
- [ ] Subdominio `bot.kinetraumadeportivo.com` en HostingPlus y actualizar el Caddyfile.
- [ ] Definir `HANDOFF_CONTACTO` (a quien deriva Kitra cuando piden una persona).
- [ ] Revisar precios y datos en `knowledge/kitradep.md`.
- [ ] Activar facturacion de Gemini y confirmar la tabla de precios de Meta para Chile.

### Antes de produccion
- [ ] Backups automaticos de la base de datos y monitoreo (UptimeRobot a `/health`).
- [ ] Migrar `google-generativeai` (sin soporte) a `google-genai`.
- [ ] Agregar `.dockerignore` para que el `.env` no quede copiado dentro de la imagen.
- [ ] Pasar a un hosting pagado antes de que venza el Free plan de AWS (~mayo 2027).
