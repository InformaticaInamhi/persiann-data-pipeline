# PERSIANN Data Pipeline

Repositorio para la descarga, procesamiento e inserción de datos satelitales de precipitación PERSIANN-CCS hacia PostgreSQL.

## Objetivo

Automatizar la ingesta de datos de precipitación PERSIANN-CCS cada 3 horas, aplicando una máscara espacial precalculada para Ecuador y almacenando los valores resultantes en la base de datos institucional.

## Fuente de datos

- Producto: PERSIANN-CCS
- Frecuencia: 3 horas
- Formato original: `.bin.gz`
- Fuente HTTP: `https://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/3hrly`

## Estructura del proyecto

```text
persiann-data-pipeline/
├── config.ini
├── config.example.ini
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── masks/
│       ├── .gitkeep
│       └── mask_Ecuador.npy
└── main/
    ├── run_persiann.py
    ├── modules/
    │   ├── __init__.py
    │   ├── config_loader.py
    │   ├── connections.py
    │   ├── logger.py
    │   └── persiann_processor.py
    └── logs/
```

## Archivo de máscara espacial

El archivo `mask_Ecuador.npy` es un insumo necesario para ejecutar el proceso.  
Debe colocarse en:

```text
data/masks/mask_Ecuador.npy
```

La ruta está configurada en `config.ini`:

```ini
[GRID]
mask_file = data/masks/mask_Ecuador.npy
```

El código resuelve esta ruta de forma relativa desde la raíz del proyecto.  
Por lo tanto, no es necesario usar rutas absolutas como:

```text
/home/jupyter-cr_mosquera/Procesos_Cron/mask_Ecuador.npy
```

## Archivos principales

### `config.ini`

Archivo local de configuración. Contiene credenciales de base de datos, parámetros de PERSIANN, ruta de la máscara espacial y parámetros generales.

Este archivo no debe subirse a GitHub.

### `config.example.ini`

Plantilla sin credenciales reales. Sirve como referencia para crear el `config.ini` en otro entorno.

### `requirements.txt`

Lista de librerías necesarias para ejecutar el pipeline.

### `main/run_persiann.py`

Archivo principal de ejecución.

### `main/modules/persiann_processor.py`

Contiene la lógica principal:

- cálculo de ventana de descarga
- construcción del nombre del archivo PERSIANN
- descarga HTTP
- descompresión `.gz`
- transformación de la grilla global
- aplicación de máscara espacial
- inserción masiva en PostgreSQL

### `main/modules/logger.py`

Implementa logs en formato ELF:

```text
Fecha y hora | Tipo | IP | Código | Mensaje | Usuario | Contexto
```

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

```bash
cp config.example.ini config.ini
```

Luego editar `config.ini` con las credenciales reales y verificar que exista:

```text
data/masks/mask_Ecuador.npy
```

## Ejecución manual

Desde la raíz del proyecto:

```bash
python main/run_persiann.py
```

## Ejecución por cron

Ejemplo cada 3 horas:

```bash
0 */3 * * * /usr/bin/python3 /ruta/persiann-data-pipeline/main/run_persiann.py >> /ruta/persiann-data-pipeline/main/logs/cron.log 2>&1
```

## Tabla destino

```text
obsrv_satelital_persiann."_017140801h"
```

La columna horaria se define automáticamente según la hora del archivo descargado:

```text
"0h", "3h", "6h", ..., "21h"
```

## Consideraciones para GitHub

Por defecto, `.gitignore` excluye:

```text
data/masks/*.npy
```

Esto evita subir archivos pesados o insumos generados.  
Si la institución decide versionar la máscara, comentar esa línea en `.gitignore`.

## Consideraciones operativas

- La máscara espacial debe existir previamente como archivo `.npy`.
- La grilla usada para generar la máscara debe coincidir con la grilla PERSIANN-CCS.
- Si no existe archivo disponible para la ventana calculada, el proceso registra el evento y finaliza sin inserción.
