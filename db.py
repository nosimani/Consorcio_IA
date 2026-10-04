"""
db.py — Capa de acceso a datos de Consorcio_IA: PostgreSQL (producción) o SQLite (desarrollo).

El motor se elige por configuración, sin tocar el resto del código:
  * Si existe DATABASE_URL (variable de entorno o secreto de Streamlit) -> PostgreSQL.
  * Si no                                                            -> SQLite en CONSORCIOS_DB
                                                                        (por defecto consorcios.db).

Ejemplo de DATABASE_URL:  postgresql://usuario:clave@host:5432/base?sslmode=require

Qué resuelve esta capa para que `modulo_cobranzas`, `mora`, `recibos` y `webhook_server`
funcionen igual en los dos motores:
  * Parámetros con `?` (se traducen a `%s` para PostgreSQL).
  * Filas con acceso por nombre y por posición (`fila["uf"]`, `fila[0]`, `dict(fila)`).
  * Un único error de integridad (`IntegrityError`) y rollback automático ante cualquier error:
    en PostgreSQL una sentencia fallida deja la transacción abortada hasta el rollback.
  * Pool de conexiones: Streamlit re-ejecuta el script en cada clic, y abrir una conexión por
    ejecución agotaría rápido el límite de conexiones de un plan gratuito.
  * Esquema por motor (identidad autoincremental, BIGINT, DOUBLE PRECISION) y su creación segura
    aunque la app y el servicio de webhooks arranquen a la vez.

Reglas para escribir SQL en este proyecto (portable a los dos motores):
  * Parámetros siempre con `?`. Nunca pongas un `?` ni un `%` dentro de un texto literal del SQL.
  * Para obtener el id de una fila nueva usá `INSERT ... RETURNING id` (no `lastrowid`).
  * Para ignorar duplicados usá `ON CONFLICT ... DO NOTHING` (no `INSERT OR IGNORE`).
  * Los dineros viajan en centavos enteros (BIGINT). Si dividís en SQL, convertí antes:
    `CAST(monto_centavos AS DOUBLE PRECISION) / 100.0`.
"""
from __future__ import annotations

import logging
import os
import re
import sqlite3
import threading
from typing import Optional

import pandas as pd

log = logging.getLogger("db")

DB_PATH = os.getenv("CONSORCIOS_DB", "consorcios.db")

# Tablas en orden de dependencia (las claves foráneas apuntan hacia arriba).
TABLAS = ("consorcios", "unidades", "pagos", "auditoria", "cargos",
          "config_mora", "recibos", "eventos_webhook")
# Tablas con columna `id` autoincremental (el resto usa como clave una columna propia).
TABLAS_CON_ID = ("consorcios", "unidades", "pagos", "auditoria", "cargos", "eventos_webhook")


class IntegrityError(Exception):
    """Violación de unicidad / clave foránea / CHECK, igual para SQLite y PostgreSQL."""


# ───────────────────────── filas ─────────────────────────
class Fila:
    """Fila de resultado: `f["col"]`, `f[0]`, `dict(f)`, `tuple(f)` y desempaquetado."""
    __slots__ = ("_idx", "_valores")

    def __init__(self, idx: dict, valores):
        self._idx = idx
        self._valores = tuple(valores)

    def __getitem__(self, clave):
        if isinstance(clave, (int, slice)):
            return self._valores[clave]
        try:
            return self._valores[self._idx[clave]]
        except KeyError:
            raise KeyError(clave) from None

    def keys(self):
        return list(self._idx)

    def get(self, clave, defecto=None):
        return self._valores[self._idx[clave]] if clave in self._idx else defecto

    def __iter__(self):
        return iter(self._valores)

    def __len__(self):
        return len(self._valores)

    def __repr__(self):
        return "Fila(" + ", ".join(f"{k}={self._valores[i]!r}" for k, i in self._idx.items()) + ")"


_IDX_CACHE: dict = {}


def _idx_de(nombres: tuple) -> dict:
    idx = _IDX_CACHE.get(nombres)
    if idx is None:
        idx = {}
        for i, n in enumerate(nombres):
            idx.setdefault(n, i)
        if len(_IDX_CACHE) < 512:
            _IDX_CACHE[nombres] = idx
    return idx


def _fila_sqlite(cursor, valores) -> Fila:
    return Fila(_idx_de(tuple(d[0] for d in cursor.description)), valores)


def _fila_factory_pg(cursor):
    """RowFactory de psycopg 3: recibe el cursor y devuelve quien construye cada fila."""
    nombres = tuple(c.name for c in cursor.description) if cursor.description else ()
    idx = _idx_de(nombres)
    return lambda valores: Fila(idx, valores)


# ───────────────────────── configuración ─────────────────────────
def url_postgres() -> Optional[str]:
    """DATABASE_URL desde el entorno o desde los secretos de Streamlit; None si no hay."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    try:                                           # Streamlit Cloud: Settings -> Secrets
        import streamlit as st
        valor = st.secrets.get("DATABASE_URL", "")
        return valor.strip() or None if isinstance(valor, str) else None
    except Exception:
        return None


def usa_postgres() -> bool:
    return url_postgres() is not None


def descripcion_motor() -> str:
    return "PostgreSQL" if usa_postgres() else f"SQLite local ({DB_PATH})"


# ───────────────────────── esquema ─────────────────────────
_DDL = """
CREATE TABLE IF NOT EXISTS consorcios (
    id {PK},
    administrador TEXT NOT NULL,
    nombre TEXT NOT NULL,
    direccion TEXT DEFAULT '',
    UNIQUE (administrador, nombre)
);
CREATE TABLE IF NOT EXISTS unidades (
    id {PK},
    consorcio_id {FK} NOT NULL REFERENCES consorcios(id),
    uf TEXT NOT NULL,
    piso TEXT DEFAULT '',
    propietario TEXT DEFAULT '',
    coeficiente DOUBLE PRECISION DEFAULT 0,
    contacto TEXT DEFAULT '',
    UNIQUE (consorcio_id, uf)
);
CREATE TABLE IF NOT EXISTS pagos (
    id {PK},
    consorcio_id {FK} NOT NULL REFERENCES consorcios(id),
    unidad_id {FK} NOT NULL REFERENCES unidades(id),
    periodo TEXT NOT NULL,
    fecha_pago TEXT NOT NULL,
    monto_centavos BIGINT NOT NULL CHECK (monto_centavos > 0),
    medio TEXT NOT NULL,
    entidad TEXT DEFAULT '',
    referencia TEXT DEFAULT '',
    nro_recibo TEXT,
    estado TEXT NOT NULL,
    origen TEXT NOT NULL,
    observaciones TEXT DEFAULT '',
    cargado_por TEXT NOT NULL,
    creado_en TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pago_ref
    ON pagos (medio, entidad, referencia) WHERE referencia <> '';
CREATE INDEX IF NOT EXISTS ix_pagos_cons_per ON pagos (consorcio_id, periodo);
CREATE INDEX IF NOT EXISTS ix_pagos_unidad ON pagos (unidad_id);
CREATE TABLE IF NOT EXISTS auditoria (
    id {PK},
    pago_id {FK}, accion TEXT, usuario TEXT, detalle TEXT, ts TEXT
);
CREATE INDEX IF NOT EXISTS ix_auditoria_pago ON auditoria (pago_id);
CREATE TABLE IF NOT EXISTS cargos (
    id {PK},
    consorcio_id {FK} NOT NULL REFERENCES consorcios(id),
    unidad_id {FK} NOT NULL REFERENCES unidades(id),
    periodo TEXT NOT NULL,
    concepto TEXT NOT NULL DEFAULT 'Expensa ordinaria',
    monto_centavos BIGINT NOT NULL CHECK (monto_centavos > 0),
    fecha_emision TEXT NOT NULL,
    vencimiento TEXT NOT NULL,
    creado_por TEXT NOT NULL,
    creado_en TEXT NOT NULL,
    UNIQUE (unidad_id, periodo, concepto)
);
CREATE INDEX IF NOT EXISTS ix_cargos_cons ON cargos (consorcio_id);
CREATE TABLE IF NOT EXISTS config_mora (
    consorcio_id {FK} PRIMARY KEY REFERENCES consorcios(id),
    tasa_mensual TEXT NOT NULL DEFAULT '0',     -- fracción decimal: '0.03' = 3 % mensual
    dias_gracia INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS recibos (
    pago_id {FK} PRIMARY KEY REFERENCES pagos(id),
    nro_recibo TEXT NOT NULL UNIQUE,
    emitido_en TEXT NOT NULL,
    emitido_por TEXT NOT NULL,
    desglose_json TEXT NOT NULL,                -- foto congelada de la imputación al emitir
    codigo TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS eventos_webhook (
    id {PK},
    administrador TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    evento_id TEXT NOT NULL,
    estado TEXT NOT NULL,            -- procesado | sin_identificar | ignorado | error
    detalle TEXT DEFAULT '',
    datos_json TEXT DEFAULT '',
    pago_id {FK},
    recibido_en TEXT NOT NULL,
    UNIQUE (administrador, proveedor, evento_id)
);
"""

_TIPOS = {
    "sqlite": {"{PK}": "INTEGER PRIMARY KEY AUTOINCREMENT", "{FK}": "INTEGER"},
    "postgres": {"{PK}": "BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", "{FK}": "BIGINT"},
}


def esquema(motor: str) -> str:
    ddl = _DDL
    for marca, tipo in _TIPOS[motor].items():
        ddl = ddl.replace(marca, tipo)
    return ddl


def _sentencias(ddl: str) -> list[str]:
    sin_comentarios = re.sub(r"--[^\n]*", "", ddl)
    return [s.strip() for s in sin_comentarios.split(";") if s.strip()]


# ───────────────────────── conexión ─────────────────────────
def _nativo(valor):
    """numpy.int64 / float64 (por ejemplo desde pandas) -> tipos de Python que los drivers aceptan."""
    if type(valor).__module__ == "numpy" and hasattr(valor, "item"):
        return valor.item()
    return valor


def _a_pg(sql: str, params) -> str:
    # psycopg usa %s: los % literales del SQL se duplican (solo cuando hay parámetros).
    return sql.replace("%", "%%").replace("?", "%s") if params else sql


class Conexion:
    """Envoltorio mínimo con la misma interfaz que usan los módulos: execute / commit / close."""

    def __init__(self, raw, motor: str, pool=None, driver=None):
        self._raw = raw
        self.motor = motor
        self._pool = pool
        self._driver = driver          # módulo psycopg (solo PostgreSQL)

    def execute(self, sql: str, params=()):
        params = tuple(_nativo(p) for p in params) if params else ()
        try:
            if self.motor == "postgres":
                return self._raw.execute(_a_pg(sql, params), params or None)
            return self._raw.execute(sql, params)
        except Exception as error:
            if self._es_integridad(error):
                self.rollback()
                raise IntegrityError(str(error)) from error
            if self._es_error_bd(error):
                self.rollback()          # PostgreSQL deja la transacción abortada tras un error
            raise

    def _es_integridad(self, error) -> bool:
        if self.motor == "sqlite":
            return isinstance(error, sqlite3.IntegrityError)
        return isinstance(error, self._driver.errors.IntegrityError)

    def _es_error_bd(self, error) -> bool:
        if self.motor == "sqlite":
            return isinstance(error, sqlite3.Error)
        return isinstance(error, self._driver.Error)

    def df(self, sql: str, params=()) -> pd.DataFrame:
        """Resultado como DataFrame (conserva las columnas aunque no haya filas)."""
        cur = self.execute(sql, params)
        columnas = [c[0] if self.motor == "sqlite" else c.name for c in cur.description]
        return pd.DataFrame([tuple(f) for f in cur.fetchall()], columns=columnas)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        try:
            self._raw.rollback()
        except Exception:
            log.exception("No se pudo hacer rollback")

    def close(self) -> None:
        raw, self._raw = self._raw, None
        if raw is None:
            return
        if self.motor == "postgres":
            try:
                raw.rollback()           # nunca devolver al pool una transacción abierta
            except Exception:
                pass
            self._pool.putconn(raw)
        else:
            raw.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


_POOL = None
_POOL_LOCK = threading.Lock()
_ESQUEMA_PG_LISTO = False


def _pool_pg(url: str):
    global _POOL
    with _POOL_LOCK:
        if _POOL is None:
            try:
                import psycopg                                   # noqa: F401
                from psycopg_pool import ConnectionPool
            except ImportError as e:
                raise RuntimeError("Para usar PostgreSQL instalá el driver: "
                                   "pip install 'psycopg[binary,pool]'") from e
            # Verificación rápida: ante clave o host incorrectos, ConnectionPool reintenta en segundo plano
            # y getconn() recién falla a los 30 s con un mensaje poco claro. Así el error real aparece
            # enseguida (y completo: usuario, host, SSL).
            psycopg.connect(url, connect_timeout=10).close()
            _POOL = ConnectionPool(
                conninfo=url,
                min_size=1,
                max_size=int(os.getenv("DB_POOL_MAX", "5")),
                kwargs={"row_factory": _fila_factory_pg,
                        "prepare_threshold": None,               # compatible con poolers en modo transacción
                        "autocommit": False},
                check=ConnectionPool.check_connection,           # descarta conexiones cortadas por el proveedor
                timeout=30,
                max_idle=300,
                name="consorcio_ia",
                open=True,
            )
        return _POOL


def get_conn(path: Optional[str] = None) -> Conexion:
    """Sin argumentos: PostgreSQL si hay DATABASE_URL, si no SQLite (DB_PATH).
    Con `path`: SQLite en esa ruta (por ejemplo ':memory:' en las pruebas)."""
    url = url_postgres() if path is None else None
    if url:
        import psycopg
        pool = _pool_pg(url)
        return Conexion(pool.getconn(), "postgres", pool=pool, driver=psycopg)
    raw = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    raw.row_factory = _fila_sqlite
    raw.execute("PRAGMA foreign_keys = ON")
    return Conexion(raw, "sqlite")


def init_db(conn: Conexion) -> None:
    """Crea las tablas si no existen. En PostgreSQL se hace una vez por proceso y con un
    candado de sesión, para que la app y el servicio de webhooks puedan arrancar a la vez."""
    global _ESQUEMA_PG_LISTO
    if conn.motor == "sqlite":
        conn._raw.executescript(esquema("sqlite"))
        conn.commit()
        return
    if _ESQUEMA_PG_LISTO:
        return
    conn.execute("SELECT pg_advisory_xact_lock(727201)")
    for sentencia in _sentencias(esquema("postgres")):
        conn.execute(sentencia)
    conn.commit()
    if os.getenv("DB_ACTIVAR_RLS", "1") == "1":
        # Defensa en profundidad (p. ej. Supabase publica el esquema `public` por una API REST):
        # con RLS activada y sin políticas, esos roles no leen nada. El dueño de las tablas
        # (el usuario de DATABASE_URL) no se ve afectado.
        for tabla in TABLAS:
            try:
                conn.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
                conn.commit()
            except Exception:
                log.warning("No se pudo activar RLS en %s (¿el usuario no es el dueño?)", tabla)
                conn.rollback()
    _ESQUEMA_PG_LISTO = True


def cerrar_pool() -> None:
    """Cierra las conexiones del pool (al apagar el servicio o al terminar un script)."""
    global _POOL, _ESQUEMA_PG_LISTO
    with _POOL_LOCK:
        if _POOL is not None:
            _POOL.close()
            _POOL = None
        _ESQUEMA_PG_LISTO = False
