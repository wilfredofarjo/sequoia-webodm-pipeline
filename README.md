# Sequoia WebODM Pipeline

Flujo reproducible para organizar, validar y preparar imágenes multiespectrales **Parrot Sequoia** antes de su procesamiento en **WebODM / OpenDroneMap**.

## Objetivo

El proyecto nació a partir de un conjunto de imágenes almacenadas entre la memoria interna de la cámara y la tarjeta SD, con fechas internas incorrectas y múltiples reinicios del reloj. El flujo permite:

- inventariar imágenes de ambas fuentes;
- identificar bandas `GRE`, `RED`, `REG`, `NIR` y `RGB`;
- excluir miniaturas `.thumb` y archivos auxiliares;
- detectar duplicados mediante SHA-256;
- identificar capturas multiespectrales completas e incompletas;
- mantener separadas las imágenes RGB del dataset multiespectral;
- reconstruir sesiones de adquisición a partir de carpeta, secuencia, reloj interno y bitácora;
- generar un dataset final compatible con WebODM.

## Resultado validado del caso de estudio

| Fecha real | Capturas completas | TIFF para WebODM |
|---|---:|---:|
| 2026-05-28 | 177 | 708 |
| 2026-07-10 | 314 | 1,256 |
| 2026-08-21 | 153 | 612 |
| **Total** | **644** | **2,576** |

Cada captura completa contiene cuatro bandas:

```text
GRE.TIF
RED.TIF
REG.TIF
NIR.TIF
```

Los archivos `RGB.JPG` se mantienen separados y no se incluyen en la tarea multiespectral inicial de WebODM.

## Estructura del repositorio

```text
sequoia-webodm-pipeline/
├── README.md
├── .gitignore
├── scripts/
│   └── sequoia_dataset_organizer.py
├── docs/
│   ├── workflow.md
│   └── webodm_configuration.md
└── examples/
    └── session_mapping.example.json
```

## Uso

El script trabaja sobre una carpeta base con:

```text
Fotos Parrot Sequoia/
├── Interna/
└── SD/
```

Ejemplo:

```bash
python3 scripts/sequoia_dataset_organizer.py \
  --base "/ruta/Fotos Parrot Sequoia" \
  --session-map examples/session_mapping.example.json
```

Por defecto funciona en modo diagnóstico. Para copiar el dataset final se debe usar explícitamente `--copy-final`.

## Principio de seguridad

Los archivos originales no se renombran, no se mueven y no se modifican. El pipeline trabaja mediante inventario, hashes y copias hacia nuevas carpetas.

## WebODM

El dataset final para WebODM contiene únicamente las bandas multiespectrales completas. Se recomienda procesar cada sesión real por separado.

Consulta `docs/webodm_configuration.md` para una configuración inicial.

## Datos no incluidos

Este repositorio no contiene TIFF/JPG originales, archivos `.dat`, nubes de puntos ni productos WebODM. Estos datos pueden ser demasiado pesados y pueden contener información experimental que no debe versionarse con Git.

## Estado

Versión inicial basada en el flujo validado hasta **v2.7** del organizador Parrot Sequoia.
