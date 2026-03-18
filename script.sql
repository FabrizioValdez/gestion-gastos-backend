-- ================================================
-- PROYECTO : Control de Gastos y Servicios
-- AUTOR    : Henry Fabrizio Valdez Zevallos
-- DB       : PostgreSQL 15+ (Supabase)
-- ACTUALIZADO: 18/03/2026
-- ================================================

-- ------------------------------------------------
-- 1. TABLA: tipo_servicio
-- ------------------------------------------------
CREATE TABLE tipo_servicio (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);

-- Seed de datos iniciales
INSERT INTO tipo_servicio (nombre) VALUES
    ('Luz'), ('Agua'), ('Internet'), ('Gas'),
    ('Linea movil'), ('Suscripcion'), ('Alquiler'), ('Otro');

-- ------------------------------------------------
-- 2. TABLA: cliente
-- ------------------------------------------------
CREATE TABLE cliente (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    correo        VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 3. TABLA: catalogo_servicio
-- ------------------------------------------------
CREATE TABLE catalogo_servicio (
    id               SERIAL PRIMARY KEY,
    tipo_servicio_id INTEGER NOT NULL
                      REFERENCES tipo_servicio(id)
                      ON DELETE RESTRICT,
    nombre           VARCHAR(100) UNIQUE NOT NULL,
    imagen_url       VARCHAR(500) NOT NULL
);

-- ------------------------------------------------
-- 4. TABLA: servicio_usuario
-- ------------------------------------------------
CREATE TABLE servicio_usuario (
    id                   SERIAL PRIMARY KEY,
    cliente_id           INTEGER NOT NULL
                         REFERENCES cliente(id)
                         ON DELETE CASCADE,
    tipo_servicio_id     INTEGER NOT NULL
                         REFERENCES tipo_servicio(id)
                         ON DELETE RESTRICT,
    catalogo_servicio_id INTEGER
                         REFERENCES catalogo_servicio(id)
                         ON DELETE SET NULL,
    nombre_servicio      VARCHAR(100),
    imagen_url           VARCHAR(500),
    monto_mensual        NUMERIC(10,2) NOT NULL
                         CHECK (monto_mensual > 0),
    dia_vencimiento      INTEGER NOT NULL DEFAULT 1
                         CHECK (dia_vencimiento >= 1 AND dia_vencimiento <= 31),
    activo               BOOLEAN DEFAULT TRUE,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW(),

    -- Regla: catalogo o manual, nunca ambos ni ninguno
    CONSTRAINT chk_nombre_o_catalogo CHECK (
        (catalogo_servicio_id IS NOT NULL AND nombre_servicio IS NULL)
        OR
        (catalogo_servicio_id IS NULL AND nombre_servicio IS NOT NULL)
    )
);

-- ------------------------------------------------
-- 5. TABLA: historial_pago
-- ------------------------------------------------
CREATE TABLE historial_pago (
    id                        SERIAL PRIMARY KEY,
    servicio_usuario_id       INTEGER NOT NULL
                              REFERENCES servicio_usuario(id)
                              ON DELETE CASCADE,
    monto_pagado              NUMERIC(10,2) NOT NULL
                              CHECK (monto_pagado > 0),
    fecha_pago                TIMESTAMP,
    fecha_vencimiento_cubierta DATE NOT NULL,
    estado                    VARCHAR(20) DEFAULT 'pendiente'
                              CHECK (estado IN ('pendiente', 'pagado')),
    created_at                TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 6. TABLA: notificacion
-- ------------------------------------------------
CREATE TABLE notificacion (
    id                  SERIAL PRIMARY KEY,
    cliente_id          INTEGER NOT NULL
                        REFERENCES cliente(id)
                        ON DELETE CASCADE,
    servicio_usuario_id INTEGER
                        REFERENCES servicio_usuario(id)
                        ON DELETE CASCADE,
    tipo                VARCHAR(30) NOT NULL
                        CHECK (tipo IN (
                            'vencimiento_proximo',
                            'pago_pendiente'
                        )),
    mensaje             TEXT NOT NULL,
    leida               BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 7. TABLA: ayuda
-- ------------------------------------------------
CREATE TABLE ayuda (
    id          SERIAL PRIMARY KEY,
    pregunta    VARCHAR(500) NOT NULL,
    respuesta   TEXT NOT NULL,
    categoria   VARCHAR(50) DEFAULT 'general',
    activa      BOOLEAN DEFAULT TRUE,
    orden       INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Seed de datos iniciales para ayuda
INSERT INTO ayuda (pregunta, respuesta, categoria, orden) VALUES
    ('¿Cómo registrar un servicio?', 'Para registrar un servicio, ve a la sección Servicios y haz clic en "Agregar Servicio". Completa los datos requeridos: tipo de servicio, nombre, monto mensual y día de vencimiento.', 'servicios', 1),
    ('¿Cómo registrar un pago?', 'Puedes registrar un pago de dos formas: 1) Desde la sección Deudas, haz clic en "Pagar Ahora". 2) Desde la sección Pagos, haz clic en "Registrar Pago".', 'pagos', 2),
    ('¿Cómo funcionan las notificaciones?', 'El sistema envía recordatorios 3 días antes del vencimiento de cada servicio. También recibirás alertas cuando tengas pagos pendientes.', 'notificaciones', 3);

-- ================================================
-- ÍNDICES
-- ================================================

-- cliente
CREATE INDEX idx_cliente_correo
    ON cliente(correo);

-- servicio_usuario
CREATE INDEX idx_su_cliente
    ON servicio_usuario(cliente_id);
CREATE INDEX idx_su_dia_vencimiento
    ON servicio_usuario(dia_vencimiento);
CREATE INDEX idx_su_activo
    ON servicio_usuario(activo);

-- historial_pago
CREATE INDEX idx_hp_servicio
    ON historial_pago(servicio_usuario_id);
CREATE INDEX idx_hp_estado
    ON historial_pago(estado);
CREATE INDEX idx_hp_fecha_pago
    ON historial_pago(fecha_pago);
CREATE INDEX idx_hp_fecha_vencimiento_cubierta
    ON historial_pago(fecha_vencimiento_cubierta);

-- notificacion
CREATE INDEX idx_notif_cliente
    ON notificacion(cliente_id);
CREATE INDEX idx_notif_leida
    ON notificacion(leida);

-- ================================================
-- FIN DEL SCRIPT
-- ================================================
