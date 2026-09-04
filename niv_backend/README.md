# Sistema Generador de NIV — NOM-001-SSP-2008

Backend profesional en Python/FastAPI para generar y administrar Números de
Identificación Vehicular (NIV) de remolques y semirremolques, conforme a la
norma mexicana **NOM-001-SSP-2008**.

## Índice

- [Estructura del proyecto](#estructura-del-proyecto)
- [Estructura del NIV](#estructura-del-niv-17-caracteres)
- [Instalación](#instalación)
- [Configuración de PostgreSQL](#configuración-de-postgresql)
- [Ejecutar el servidor](#ejecutar-el-servidor)
- [Ejecutar las pruebas](#ejecutar-las-pruebas)
- [Documentación de endpoints](#documentación-de-endpoints)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Decisiones de diseño](#decisiones-de-diseño)

## Estructura del proyecto

```
niv_backend/
├── app/
│   ├── main.py                 # App FastAPI, middlewares, manejo de errores
│   ├── config.py                # Configuración (.env) vía pydantic-settings
│   ├── database.py              # Motor y sesión SQLAlchemy (PostgreSQL)
│   ├── models.py                # Modelos SQLAlchemy (niv, configuracion, mapeo_vds, serie_contador)
│   ├── schemas.py                # Schemas Pydantic de entrada/salida
│   ├── core/
│   │   ├── niv_generator.py      # Generación + persistencia atómica de NIV
│   │   ├── niv_validator.py      # Validación de formato/dígito verificador
│   │   ├── check_digit.py        # Algoritmo del dígito verificador (ISO 3779)
│   │   └── rate_limit.py         # Configuración de slowapi (rate limiting)
│   ├── api/endpoints/
│   │   ├── niv.py                # POST /niv/generate, GET /niv/{niv}
│   │   ├── search.py             # GET /niv/search
│   │   └── export.py             # POST /export/excel, POST /export/dxf
│   └── utils/
│       ├── exporters.py          # Exportación a Excel y DXF
│       └── helpers.py            # Códigos de año, formateo de serie, etc.
├── scripts/
│   ├── init_db.sql               # Script SQL directo de inicialización
│   └── init_db.py                # Script Python (SQLAlchemy) de inicialización
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Estructura del NIV (17 caracteres)

| Posición | Sección | Descripción |
|---|---|---|
| 1-3 | WMI | Identificador del fabricante (configurable, ej. `3M1`) |
| 4 | VDS | Tipo de remolque (A=Caja, B=Plataforma, C=Tolva, D=Refrigerado, ...) |
| 5 | VDS | Número de ejes (1-9) |
| 6 | VDS | Capacidad (A=<20t, B=20-30t, C=30-40t, D=>40t) |
| 7 | VDS | Tipo de frenos (1=Neumático, 2=Hidráulico, 3=Eléctrico) |
| 8 | VDS | Versión (1=Estándar, 2=Premium, 3=Especial) |
| 9 | Check digit | Calculado automáticamente (suma ponderada módulo 11) |
| 10 | VIS | Año modelo (ciclo de 30 años, ej. T=2026, V=2027, W=2028) |
| 11 | VIS | Planta (A=única planta, preparado para B, C, D...) |
| 12 | VIS | Línea de producción (1-9) |
| 13-17 | VIS | Serie secuencial (00001-99999), autoincremental por línea/año |

Las posiciones 4, 6, 7 y 8 se resuelven mediante la tabla `mapeo_vds`, por lo
que se pueden agregar/editar/desactivar códigos **sin tocar código fuente**.

> **Nota sobre nombres de campo:** para evitar problemas de codificación con
> el carácter `ñ` en identificadores de Python, variables de entorno y
> nombres de columna, internamente se usa `anio_modelo` (ASCII). La API
> pública sigue aceptando y devolviendo el campo `año_modelo` en el JSON,
> tal como se especificó (ver `schemas.py`, alias de Pydantic).

## Instalación

Requiere **Python 3.10+** y **PostgreSQL 13+**.

```bash
cd niv_backend
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Editar con las credenciales reales
```

## Configuración de PostgreSQL

1. Crear la base de datos:

   ```bash
   createdb niv_db
   ```

2. Ajustar `DATABASE_URL` en `.env`:

   ```
   DATABASE_URL=postgresql://usuario:password@localhost:5432/niv_db
   ```

3. Inicializar tablas y datos (elige una opción):

   ```bash
   # Opción A: SQL directo
   psql -U usuario -d niv_db -f scripts/init_db.sql

   # Opción B: script Python (usa la configuración de .env)
   python scripts/init_db.py
   ```

## Ejecutar el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Ejecutar las pruebas

Las pruebas usan SQLite en memoria (no requieren PostgreSQL):

```bash
pytest -v
```

## Documentación de endpoints

Todos los endpoints están bajo el prefijo `/api/v1` y responden con la
envoltura estándar `{"success": bool, "data": ..., "error": ...}`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/niv/generate` | Genera y persiste un nuevo NIV |
| GET | `/api/v1/niv/{niv}` | Obtiene el detalle de un NIV registrado |
| GET | `/api/v1/niv/search` | Búsqueda paginada con filtros múltiples |
| POST | `/api/v1/export/excel` | Exporta resultados filtrados a `.xlsx` |
| POST | `/api/v1/export/dxf` | Exporta uno o varios NIV a `.dxf` (láser) |
| GET | `/health` | Verificación de salud del servicio |

## Ejemplos de uso

```bash
# Iniciar servidor
uvicorn app.main:app --reload --port 8000

# Generar NIV
curl -X POST http://localhost:8000/api/v1/niv/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_remolque": "A",
    "num_ejes": 2,
    "capacidad": "B",
    "tipo_frenos": "1",
    "version": "1",
    "año_modelo": 2026,
    "linea_produccion": 1
  }'

# Buscar NIV
curl "http://localhost:8000/api/v1/niv/search?tipo_remolque=A&limit=10"

# Exportar a Excel
curl -X POST http://localhost:8000/api/v1/export/excel \
  -H "Content-Type: application/json" \
  -d '{"filters": {"año_modelo": 2026}}' \
  --output remolques_2026.xlsx

# Exportar a DXF (batch)
curl -X POST http://localhost:8000/api/v1/export/dxf \
  -H "Content-Type: application/json" \
  -d '{"nivs": ["3M1A2B111TA100001", "3M1A2B111TA100002"], "config": {"batch": true}}' \
  --output niv_batch.dxf
```

## Decisiones de diseño

- **Serie atómica por línea/año:** se usa una tabla `serie_contador` con
  `SELECT ... FOR UPDATE` para incrementar de forma segura bajo concurrencia
  (evita condiciones de carrera al generar NIVs en paralelo).
- **Dígito verificador:** implementado en `app/core/check_digit.py` siguiendo
  exactamente los pesos y la tabla de transliteración de la norma. Cubierto
  con pruebas unitarias con vectores calculados a mano (incluye el caso
  residuo=10 → `X`).
- **Tablas de mapeo configurables:** `mapeo_vds` permite agregar nuevos tipos
  de remolque, capacidades, frenos o versiones sin desplegar código nuevo.
  Los códigos inactivos (`activo=false`) se ignoran en la generación.
- **Multi-planta:** el campo `planta` es parametrizable por request (o usa
  `PLANTA_DEFAULT`), preparado para múltiples plantas futuras.
- **Rate limiting:** `slowapi` limita `/niv/generate` a 60 solicitudes/minuto
  por IP (configurable en `app/api/endpoints/niv.py`).
- **DXF para láser:** cada carácter se dibuja como una entidad `TEXT`
  independiente en la capa `NIV` (color ACI 7), centrada en el origen, con
  espaciado configurable entre caracteres — apto para máquinas de grabado.
