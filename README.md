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

## Generación y uso de `mask_Ecuador.npy`

El archivo `mask_Ecuador.npy` es un insumo necesario para ejecutar el proceso. Esta máscara espacial permite limitar el procesamiento de la grilla global PERSIANN-CCS únicamente al territorio de Ecuador.

Debe colocarse en:

```text
data/masks/mask_Ecuador.npy
```

La ruta está configurada en `config.ini`:

```ini
[GRID]
mask_file = data/masks/mask_Ecuador.npy
```

El código resuelve esta ruta de forma relativa desde la raíz del proyecto. Por lo tanto, no es necesario usar rutas absolutas como:

```text
/home/jupyter-cr_mosquera/Procesos_Cron/mask_Ecuador.npy
```

### Límite geográfico utilizado

La máscara fue generada a partir del archivo vectorial:

```text
Ecuador_sin_divisiones.gpkg
```

Este archivo contiene el límite geográfico de Ecuador sin divisiones administrativas internas.

El sistema de referencia utilizado es:

```text
CRS: WGS 84
EPSG: 4326
```

En caso de que el archivo vectorial original se encuentre en otro sistema de coordenadas, debe reproyectarse previamente a `EPSG:4326`, debido a que la grilla PERSIANN-CCS se procesa en coordenadas geográficas de latitud y longitud.

### Grilla PERSIANN de referencia

La máscara se genera sobre la misma grilla espacial utilizada por los archivos binarios de PERSIANN-CCS.

Características esperadas:

```text
Producto: PERSIANN-CCS
Resolución espacial: 0.04°
Dimensiones esperadas del arreglo: 3000 x 9000
Formato de grilla: global
Sistema de coordenadas: geográfico, EPSG:4326
```

El archivo `mask_Ecuador.npy` debe tener las mismas dimensiones que el arreglo de precipitación PERSIANN procesado antes de aplicar la máscara.

### Método de generación

Para generar la máscara, se evalúa cada celda de la grilla PERSIANN-CCS y se determina si el centro de la celda se encuentra dentro del polígono correspondiente al límite geográfico de Ecuador.

Las celdas ubicadas dentro del límite nacional se marcan como válidas, mientras que las celdas fuera del límite se excluyen del procesamiento.

El resultado se almacena como un arreglo NumPy:

```text
mask_Ecuador.npy
```

Este archivo permite reutilizar la máscara en cada ejecución del pipeline sin recalcular la intersección espacial, reduciendo el tiempo de procesamiento.

### Uso dentro del pipeline

Durante la ejecución del pipeline, el archivo `mask_Ecuador.npy` se carga desde la ruta configurada y se aplica sobre el arreglo de precipitación PERSIANN-CCS ya transformado.

De forma conceptual, el proceso realiza lo siguiente:

```python
mask = np.load("data/masks/mask_Ecuador.npy")
precip_ecuador = np.where(mask, precip_array, np.nan)
```

De esta manera, únicamente se conservan los valores de precipitación correspondientes a las celdas ubicadas dentro del territorio de Ecuador.

### Validación de la máscara

Antes de utilizar la máscara en operación, se deben realizar las siguientes validaciones:

1. Verificar que las dimensiones de la máscara coincidan con las dimensiones del arreglo PERSIANN procesado:

```python
mask.shape == precip_array.shape
```

2. Confirmar que el archivo vectorial utilizado para generar la máscara se encuentre en `EPSG:4326`.

3. Verificar visualmente la superposición de la máscara sobre el límite geográfico de Ecuador.

4. Revisar el número de celdas activas dentro de la máscara. Para la grilla PERSIANN-CCS de 0.04° utilizada en este pipeline, se espera aproximadamente:

```text
12963 celdas activas
```

5. Validar que puntos o estaciones conocidas dentro de Ecuador coincidan con celdas activas de la máscara.

Si el número de celdas activas cambia significativamente, se debe revisar el CRS del archivo vectorial, el orden de latitudes y longitudes, la transformación aplicada al arreglo PERSIANN y la resolución espacial utilizada.


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
