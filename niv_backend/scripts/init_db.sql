-- Script de inicialización de base de datos para el Sistema Generador de NIV.
-- Ejecutar contra una base de datos PostgreSQL vacía:
--   psql -U <usuario> -d niv_db -f scripts/init_db.sql

CREATE TABLE IF NOT EXISTS niv (
    id SERIAL PRIMARY KEY,
    niv VARCHAR(17) UNIQUE NOT NULL,
    wmi VARCHAR(3) NOT NULL,
    vds VARCHAR(5) NOT NULL,
    digito_verificador CHAR(1) NOT NULL,
    vis VARCHAR(8) NOT NULL,
    tipo_remolque VARCHAR(50) NOT NULL,
    num_ejes INTEGER NOT NULL CHECK (num_ejes BETWEEN 1 AND 9),
    capacidad VARCHAR(10) NOT NULL,
    tipo_frenos VARCHAR(20) NOT NULL,
    version VARCHAR(20) NOT NULL,
    anio_modelo INTEGER NOT NULL,
    codigo_anio CHAR(1) NOT NULL,
    planta CHAR(1) NOT NULL,
    linea_produccion INTEGER NOT NULL,
    numero_serie INTEGER NOT NULL,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_linea_anio_serie UNIQUE (linea_produccion, anio_modelo, numero_serie)
);

CREATE INDEX IF NOT EXISTS idx_niv ON niv(niv);
CREATE INDEX IF NOT EXISTS idx_fecha ON niv(fecha_generacion);
CREATE INDEX IF NOT EXISTS idx_tipo ON niv(tipo_remolque);
CREATE INDEX IF NOT EXISTS idx_anio ON niv(anio_modelo);

CREATE TABLE IF NOT EXISTS configuracion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(50) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(20) DEFAULT 'string',
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO configuracion (clave, valor, descripcion, tipo) VALUES
    ('wmi', '3M1', 'Identificador Mundial del Fabricante', 'string'),
    ('planta_default', 'A', 'Código de planta por defecto', 'string'),
    ('anio_inicio', '2026', 'Año de inicio de operaciones', 'integer'),
    ('dxf_altura_texto', '3', 'Altura de texto en DXF (mm)', 'float'),
    ('dxf_espaciado', '0.5', 'Espaciado entre caracteres DXF (mm)', 'float')
ON CONFLICT (clave) DO NOTHING;

CREATE TABLE IF NOT EXISTS mapeo_vds (
    id SERIAL PRIMARY KEY,
    posicion INTEGER NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    UNIQUE(posicion, codigo)
);

INSERT INTO mapeo_vds (posicion, codigo, descripcion, categoria) VALUES
    (4, 'A', 'Caja seca', 'tipo_remolque'),
    (4, 'B', 'Plataforma', 'tipo_remolque'),
    (4, 'C', 'Tolva', 'tipo_remolque'),
    (4, 'D', 'Refrigerado', 'tipo_remolque'),
    (6, 'A', 'Menos de 20 toneladas', 'capacidad'),
    (6, 'B', '20-30 toneladas', 'capacidad'),
    (6, 'C', '30-40 toneladas', 'capacidad'),
    (6, 'D', 'Más de 40 toneladas', 'capacidad'),
    (7, '1', 'Neumático', 'tipo_frenos'),
    (7, '2', 'Hidráulico', 'tipo_frenos'),
    (7, '3', 'Eléctrico', 'tipo_frenos'),
    (8, '1', 'Estándar', 'version'),
    (8, '2', 'Premium', 'version'),
    (8, '3', 'Especial', 'version')
ON CONFLICT (posicion, codigo) DO NOTHING;

-- Contador atómico de serie secuencial, independiente por línea de producción y año modelo.
CREATE TABLE IF NOT EXISTS serie_contador (
    id SERIAL PRIMARY KEY,
    linea_produccion INTEGER NOT NULL,
    anio_modelo INTEGER NOT NULL,
    ultimo_numero INTEGER NOT NULL DEFAULT 0,
    UNIQUE(linea_produccion, anio_modelo)
);
