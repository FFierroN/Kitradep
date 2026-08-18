"""Backup de la base de datos SQLite.

Hace una copia con timestamp de la DB y rota las copias viejas segun la
retencion configurada. Opcionalmente sube la copia a Backblaze B2 (u otro
storage S3-compatible) si boto3 esta instalado y hay credenciales.

Uso local:
    python scripts/backup.py

Uso en cron (VPS), todos los dias a las 3 AM:
    0 3 * * *  cd /app && python scripts/backup.py >> /var/log/kitradep_backup.log 2>&1

Variables de entorno para subida a B2 (opcionales):
    B2_ENDPOINT_URL   ej: https://s3.us-west-004.backblazeb2.com
    B2_BUCKET         ej: kitradep-backups
    B2_KEY_ID
    B2_APP_KEY
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Permite importar config desde la carpeta padre.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config  # noqa: E402

RETENCION_DIAS = int(os.getenv("BACKUP_RETENCION_DIAS", "30"))
DIR_BACKUPS = Path(os.getenv("BACKUP_DIR", str(config.db_path.parent / "backups")))


def crear_backup_local() -> Path | None:
    """Copia la DB a la carpeta de backups con timestamp. Devuelve la ruta."""
    if not config.db_path.exists():
        print(f"[backup] No existe la DB en {config.db_path}, nada que respaldar.")
        return None

    DIR_BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destino = DIR_BACKUPS / f"kitradep_{ts}.db"
    shutil.copy2(config.db_path, destino)
    print(f"[backup] Copia local creada: {destino} ({destino.stat().st_size} bytes)")
    return destino


def rotar_backups() -> None:
    """Borra copias mas viejas que la retencion configurada."""
    if not DIR_BACKUPS.exists():
        return
    ahora = datetime.now(timezone.utc).timestamp()
    limite = ahora - RETENCION_DIAS * 86400
    borrados = 0
    for f in DIR_BACKUPS.glob("kitradep_*.db"):
        if f.stat().st_mtime < limite:
            f.unlink()
            borrados += 1
    if borrados:
        print(f"[backup] Rotacion: {borrados} copias viejas borradas.")


def subir_a_b2(archivo: Path) -> bool:
    """Sube el backup a Backblaze B2 (S3-compat) si esta configurado."""
    endpoint = os.getenv("B2_ENDPOINT_URL")
    bucket = os.getenv("B2_BUCKET")
    key_id = os.getenv("B2_KEY_ID")
    app_key = os.getenv("B2_APP_KEY")
    if not all([endpoint, bucket, key_id, app_key]):
        print("[backup] B2 no configurado (variables faltantes). Solo copia local.")
        return False

    try:
        import boto3  # import lazy: solo si se usa
    except ImportError:
        print("[backup] boto3 no instalado. Instalalo con: pip install boto3")
        return False

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key,
        )
        s3.upload_file(str(archivo), bucket, archivo.name)
        print(f"[backup] Subido a B2: s3://{bucket}/{archivo.name}")
        return True
    except Exception as exc:  # pragma: no cover - depende de red
        print(f"[backup] Error subiendo a B2: {type(exc).__name__}: {exc}")
        return False


def main() -> None:
    print(f"[backup] Iniciando backup - {datetime.now(timezone.utc).isoformat()}")
    copia = crear_backup_local()
    if copia:
        subir_a_b2(copia)
    rotar_backups()
    print("[backup] Listo.")


if __name__ == "__main__":
    main()
