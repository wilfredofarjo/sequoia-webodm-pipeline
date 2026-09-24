# Configuración inicial de WebODM

Esta configuración está orientada a imágenes Parrot Sequoia tomadas a corta distancia sobre plantas en ambiente controlado.

## Dataset de entrada

Cargar únicamente:

```text
GRE.TIF
RED.TIF
REG.TIF
NIR.TIF
```

No incluir inicialmente `RGB.JPG`.

## Parámetros iniciales sugeridos

| Parámetro | Valor inicial |
|---|---|
| feature-quality | high |
| pc-quality | medium |
| sfm-algorithm | incremental |
| radiometric-calibration | camera+sun |
| skip-band-alignment | false |
| primary-band | rededge |
| matcher-neighbors | 8–10 |
| dsm | false durante diagnóstico |
| dtm | false |
| 3D model | false durante diagnóstico |

## Criterio de éxito inicial

Antes de densificar la nube o generar modelos 3D, comprobar:

1. una única reconstrucción SfM principal;
2. alineamiento correcto entre bandas;
3. ausencia de imágenes RGB dentro del conjunto multiespectral;
4. consistencia de la sesión temporal.

## Índices posteriores

Una vez alineadas las bandas:

```text
NDVI  = (NIR - RED) / (NIR + RED)
NDRE  = (NIR - REG) / (NIR + REG)
GNDVI = (NIR - GRE) / (NIR + GRE)
```
