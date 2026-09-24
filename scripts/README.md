# Scripts

El pipeline de organización fue validado experimentalmente hasta la versión **v2.7**.

La versión pública debe mantenerse sin rutas locales codificadas y ejecutarse con una carpeta base suministrada por el usuario, por ejemplo:

```bash
python3 sequoia_dataset_organizer.py \
  --base "/ruta/Fotos Parrot Sequoia"
```

La carpeta base debe contener:

```text
Fotos Parrot Sequoia/
├── Interna/
└── SD/
```

Para seguridad, el modo por defecto debe ser diagnóstico. La creación/copia del dataset final debe requerir una opción explícita como `--copy-final`.

## Reglas de publicación

No incluir en Git:

- rutas absolutas del equipo local;
- imágenes TIFF/JPG experimentales;
- archivos `.dat`;
- ZIP originales;
- productos WebODM;
- manifiestos con rutas locales reales.

La lógica estable validada incluye:

1. inventario recursivo;
2. exclusión de `.thumb`;
3. identificación GRE/RED/REG/NIR/RGB;
4. SHA-256;
5. detección de capturas completas;
6. reconstrucción de sesiones;
7. validación contra bitácora;
8. preparación por fecha para WebODM.
