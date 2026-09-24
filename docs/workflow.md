# Workflow

## 1. Adquisición

Cada disparo Parrot Sequoia puede producir:

- GRE — Green
- RED — Red
- REG — Red Edge
- NIR — Near Infrared
- RGB — imagen RGB de referencia

Para WebODM, el conjunto multiespectral se procesa con GRE + RED + REG + NIR.

## 2. Inventario

El pipeline recorre recursivamente `Interna/` y `SD/`.

Se excluyen:

- `.thumb`
- `Zip_Originales`
- `__MACOSX`
- carpetas de salida del propio pipeline

## 3. Validación de capturas

Una captura multiespectral se considera completa si contiene:

```text
GRE + RED + REG + NIR
```

El RGB no es requisito para considerar completa una captura.

## 4. Duplicados

Se usa SHA-256 para identificar archivos idénticos sin depender de fechas o nombres.

## 5. Reconstrucción de sesiones

Debido a reinicios del reloj de la cámara, la fecha embebida no se trata como verdad experimental.

Se utilizan:

- fuente: INTERNA o SD;
- carpeta original;
- nombre base;
- secuencia embebida;
- continuidad temporal;
- bitácora de campo.

La bitácora validó tres fechas reales:

```text
2026-05-28
2026-07-10
2026-08-21
```

## 6. Dataset final

El resultado esperado es:

```text
Sesion_YYYY-MM-DD/
├── WebODM_Multiespectral/
└── RGB_Referencia/
```

Las capturas incompletas se mantienen fuera de `WebODM_Multiespectral`.

## 7. Trazabilidad

Se recomienda conservar siempre:

- nombre original;
- ruta original;
- fuente;
- carpeta original;
- SHA-256;
- ID normalizado de captura;
- fecha experimental final.
