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
- reconstruir sesiones de adquisición usando fuente, carpeta y bitácora;
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
│   ├── README.md
│   └── sequoia_dataset_organizer.py
├── docs/
│   ├── workflow.md
│   └── webodm_configuration.md
└── examples/
    ├── session_mapping.example.json
    └── session_mapping_by_folder.example.json
```

## Requisitos

- Python 3.9 o superior
- No requiere paquetes externos

## Uso

La carpeta base debe contener:

```text
Fotos Parrot Sequoia/
├── Interna/
└── SD/
```

### 1. Diagnóstico

```bash
python3 scripts/sequoia_dataset_organizer.py \
  --base "/ruta/Fotos Parrot Sequoia"
```

Esto genera reportes CSV sin copiar ni modificar fotografías.

### 2. Asignación de fechas mediante bitácora

El ejemplo validado usa rangos de carpetas por fuente:

```bash
python3 scripts/sequoia_dataset_organizer.py \
  --base "/ruta/Fotos Parrot Sequoia" \
  --session-map examples/session_mapping_by_folder.example.json
```

Formato del JSON:

```json
{
  "2026-05-28": [
    {
      "source": "INTERNA",
      "folder_start": 51,
      "folder_end": 215
    }
  ]
}
```

### 3. Crear el dataset final

La copia final requiere explícitamente `--copy-final` y un mapa de sesiones:

```bash
python3 scripts/sequoia_dataset_organizer.py \
  --base "/ruta/Fotos Parrot Sequoia" \
  --session-map examples/session_mapping_by_folder.example.json \
  --copy-final
```

Opcionalmente:

```bash
--no-rgb
--no-incomplete
```

## Salida

Los reportes se guardan en:

```text
Sequoia_Organizado/Reportes/
├── captures.csv
├── duplicates.csv
├── unrecognized.csv
├── final_manifest.csv
└── summary_by_real_date.csv
```

Cuando se usa `--copy-final`:

```text
Sequoia_Organizado/
└── Sequoia_Final_WebODM/
    ├── Sesion_YYYY-MM-DD/
    │   ├── WebODM_Multiespectral/
    │   └── RGB_Referencia/
    └── Capturas_Incompletas/
```

## Principio de seguridad

Los archivos originales no se renombran, no se mueven y no se modifican. El pipeline trabaja mediante inventario, hashes y copias hacia nuevas carpetas.

## WebODM

El dataset final para WebODM contiene únicamente las bandas multiespectrales completas. Se recomienda procesar cada sesión real por separado.

Consulta `docs/webodm_configuration.md` para una configuración inicial.

## Datos no incluidos

Este repositorio no contiene TIFF/JPG originales, archivos `.dat`, nubes de puntos ni productos WebODM.

## Versión

**v0.1.0** — primera versión pública del organizador, derivada del flujo experimental validado hasta v2.7.
