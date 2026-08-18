# Motor del chatbot - Fase 2

Interprete que lee `flujo/guion.yaml` y ejecuta la conversacion en la
terminal. Contenido separado de logica: para editar lo que dice el bot
tocas el YAML, para cambiar el comportamiento tocas `motor.py`.

## Como correrlo

```bash
# Desde la carpeta chatbot/
python motor.py

# Con delay simulado desactivado (util para tests):
python motor.py --sin-delay

# Con otro guion:
python motor.py --guion flujo/mi_otro_guion.yaml
```

## Comandos globales (funcionan en cualquier momento)

| Escribes | Que hace |
|---|---|
| `menu`, `inicio`, `reset` | Vuelve al estado inicial |
| `salir`, `exit`, `quit`, `chao` | Salta a la despedida |
| Ctrl+C | Corta la conversacion limpiamente |

## Arquitectura interna

```
motor.py
+-- Guion         (dataclass)   carga el YAML
+-- Tipeador                    simula "escribiendo..." con delay
+-- Conversacion  (dataclass)   estado + variables + loop principal
|     +-- formatear()           reemplaza {variables} en textos
|     +-- procesar_menu()       matching por palabras clave (case-insensitive)
|     +-- procesar_entrada()    guarda respuesta libre
|     +-- es_comando_global()   menu/salir en cualquier estado
|     +-- ejecutar()            loop principal
+-- main() + CLI                argparse + arranque
```

## Como se resuelven los inputs del usuario

1. Se normaliza a minusculas y se quitan espacios.
2. Se compara con las palabras de `detecta:` (igualdad O substring).
3. Si matcheo -> guarda `valor` en la variable indicada por `guardar_en` (si aplica) y transiciona a `ir_a`.
4. Si NO matcheo -> muestra `globales.no_entiendo` y repite el mismo estado.

## Variables recolectadas (definidas en el guion)

- `{prevision}`   -> Fonasa / Isapre / Particular
- `{plan}`        -> texto con la modalidad + precio elegido
- `{horario_pref}` -> AM / PM / Cualquiera
- `{datos}`       -> bloque completo de datos del paciente (texto libre)

Ademas todas las claves de `config` quedan disponibles como variables
(ej: `{nombre_bot}`).

## Que NO hace todavia

- No conecta con WhatsApp (Fase 4).
- No usa IA generativa (Fase 3, opcional).
- No persiste conversaciones en BD (se pierde al cerrar).
- No maneja multiples usuarios en paralelo.
- No valida formato de datos (RUT, email, telefono) - solo los guarda literal.

## Fases del proyecto

- Fase 1 -> Diseno del flujo + guion en YAML (LISTO)
- Fase 2 -> Motor local en terminal (LISTO - este)
- Fase 3 -> Modo hibrido con LLM (opcional, requiere API key)
- Fase 4 -> Integracion con WhatsApp (Twilio / Meta Cloud API)
