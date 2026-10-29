"""Conexão com o banco SQLite e criação das tabelas."""
import os
import sqlite3
import sys


def _pasta_gravavel(pasta):
    try:
        teste = os.path.join(pasta, ".teste_escrita")
        with open(teste, "w") as f:
            f.write("ok")
        os.remove(teste)
        return True
    except OSError:
        return False


def pasta_base():
    """Pasta onde o banco fica.

    Preferência: a mesma pasta do executável (facilita backup).
    Se ela não permitir gravação (ex.: C:\\Program Files), usa
    %LOCALAPPDATA%\\GestaoFichas, que sempre é gravável no Windows 11.
    """
    if getattr(sys, "frozen", False):
        pasta = os.path.dirname(sys.executable)
    else:
        pasta = os.path.dirname(os.path.abspath(__file__))
    if _pasta_gravavel(pasta):
        return pasta
    alternativa = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GestaoFichas"
    )
    os.makedirs(alternativa, exist_ok=True)
    return alternativa


CAMINHO_BANCO = os.path.join(pasta_base(), "fichas.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    categoria TEXT    NOT NULL DEFAULT 'Geral',
    preco     REAL    NOT NULL CHECK (preco >= 0),
    estoque   INTEGER NOT NULL DEFAULT 0,
    ativo     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fichas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    numero     TEXT    NOT NULL,
    cliente    TEXT    NOT NULL DEFAULT '',
    status     TEXT    NOT NULL DEFAULT 'ABERTA' CHECK (status IN ('ABERTA', 'FECHADA')),
    aberta_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    fechada_em TEXT,
    total      REAL    NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS itens_ficha (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ficha_id       INTEGER NOT NULL REFERENCES fichas(id) ON DELETE CASCADE,
    produto_id     INTEGER NOT NULL REFERENCES produtos(id),
    quantidade     INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario REAL    NOT NULL,
    cancelado      INTEGER NOT NULL DEFAULT 0,
    lancado_em     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_itens_ficha ON itens_ficha(ficha_id);
CREATE INDEX IF NOT EXISTS idx_fichas_status ON fichas(status);
"""


def conectar(caminho=None):
    conn = sqlite3.connect(caminho or CAMINHO_BANCO)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
