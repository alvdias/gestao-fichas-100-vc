"""Regras de negócio: produtos, comandas, lançamentos, fechamento e relatório."""
from datetime import date


class ErroNegocio(Exception):
    """Erro de regra que deve ser mostrado ao usuário."""


def moeda(valor):
    """Formata no padrão brasileiro: R$ 1.234,56"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ler_valor(texto):
    """Converte '12,50' ou '12.50' ou 'R$ 1.234,50' em float."""
    t = str(texto).replace("R$", "").strip()
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        raise ErroNegocio("Valor inválido. Use, por exemplo, 12,50")


PRODUTOS_EXEMPLO = [
    ("Cerveja Lata 350ml", "Cervejas", 7.00, 48),
    ("Cerveja Long Neck", "Cervejas", 10.00, 36),
    ("Cerveja 600ml", "Cervejas", 14.00, 24),
    ("Chopp 300ml", "Cervejas", 9.00, 100),
    ("Caipirinha", "Drinks", 18.00, 50),
    ("Dose de Cachaça", "Drinks", 6.00, 60),
    ("Refrigerante Lata", "Sem álcool", 6.00, 48),
    ("Água sem gás", "Sem álcool", 4.00, 48),
    ("Porção de Batata", "Porções", 32.00, 20),
    ("Porção de Calabresa", "Porções", 38.00, 20),
    ("Pastel (unid.)", "Porções", 8.00, 40),
]


class Sistema:
    def __init__(self, conn):
        self.conn = conn

    # ------------------------------------------------------------ produtos
    def listar_produtos(self, busca="", incluir_inativos=False):
        sql = "SELECT * FROM produtos WHERE nome LIKE ?"
        if not incluir_inativos:
            sql += " AND ativo = 1"
        sql += " ORDER BY categoria, nome"
        return self.conn.execute(sql, (f"%{busca.strip()}%",)).fetchall()

    def categorias(self):
        rows = self.conn.execute(
            "SELECT DISTINCT categoria FROM produtos WHERE ativo = 1 ORDER BY categoria"
        ).fetchall()
        return [r["categoria"] for r in rows]

    def obter_produto(self, produto_id):
        return self.conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()

    def salvar_produto(self, nome, categoria, preco, estoque, produto_id=None):
        nome = nome.strip()
        categoria = categoria.strip() or "Geral"
        if not nome:
            raise ErroNegocio("Informe o nome do produto.")
        if preco < 0:
            raise ErroNegocio("O preço não pode ser negativo.")
        existe = self.conn.execute(
            "SELECT id FROM produtos WHERE nome = ? COLLATE NOCASE AND id IS NOT ?",
            (nome, produto_id),
        ).fetchone()
        if existe:
            raise ErroNegocio(f"Já existe um produto chamado '{nome}'.")
        with self.conn:
            if produto_id:
                self.conn.execute(
                    "UPDATE produtos SET nome=?, categoria=?, preco=?, estoque=? WHERE id=?",
                    (nome, categoria, preco, int(estoque), produto_id),
                )
                return produto_id
            cur = self.conn.execute(
                "INSERT INTO produtos (nome, categoria, preco, estoque) VALUES (?, ?, ?, ?)",
                (nome, categoria, preco, int(estoque)),
            )
            return cur.lastrowid

    def entrada_estoque(self, produto_id, quantidade):
        if quantidade == 0:
            raise ErroNegocio("Informe uma quantidade diferente de zero.")
        with self.conn:
            self.conn.execute(
                "UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (int(quantidade), produto_id)
            )

    def alternar_ativo(self, produto_id):
        with self.conn:
            self.conn.execute("UPDATE produtos SET ativo = 1 - ativo WHERE id = ?", (produto_id,))

    def estoque_disponivel(self, produto_id):
        """Estoque menos o que já está lançado em comandas abertas."""
        row = self.conn.execute(
            """
            SELECT p.estoque - COALESCE((
                SELECT SUM(i.quantidade) FROM itens_ficha i
                JOIN fichas f ON f.id = i.ficha_id
                WHERE i.produto_id = p.id AND i.cancelado = 0 AND f.status = 'ABERTA'
            ), 0) AS disponivel
            FROM produtos p WHERE p.id = ?
            """,
            (produto_id,),
        ).fetchone()
        return row["disponivel"] if row else 0

    def carregar_exemplos(self):
        with self.conn:
            for nome, cat, preco, est in PRODUTOS_EXEMPLO:
                self.conn.execute(
                    "INSERT OR IGNORE INTO produtos (nome, categoria, preco, estoque) VALUES (?, ?, ?, ?)",
                    (nome, cat, preco, est),
                )

    def tem_produtos(self):
        return self.conn.execute("SELECT 1 FROM produtos LIMIT 1").fetchone() is not None

    # ------------------------------------------------------------ comandas
    def abrir_ficha(self, numero, cliente=""):
        numero = str(numero).strip()
        if not numero:
            raise ErroNegocio("Informe o número da comanda ou da mesa.")
        aberta = self.conn.execute(
            "SELECT id FROM fichas WHERE numero = ? COLLATE NOCASE AND status = 'ABERTA'", (numero,)
        ).fetchone()
        if aberta:
            raise ErroNegocio(f"A comanda {numero} já está aberta.")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO fichas (numero, cliente) VALUES (?, ?)", (numero, cliente.strip())
            )
            return cur.lastrowid

    def fichas_abertas(self):
        return self.conn.execute(
            """
            SELECT f.*, COALESCE(SUM(CASE WHEN i.cancelado = 0
                                     THEN i.quantidade * i.preco_unitario END), 0) AS parcial,
                   COALESCE(SUM(CASE WHEN i.cancelado = 0 THEN i.quantidade END), 0) AS qtd_itens
            FROM fichas f LEFT JOIN itens_ficha i ON i.ficha_id = f.id
            WHERE f.status = 'ABERTA'
            GROUP BY f.id
            ORDER BY CAST(f.numero AS INTEGER), f.numero
            """
        ).fetchall()

    def obter_ficha(self, ficha_id):
        return self.conn.execute("SELECT * FROM fichas WHERE id = ?", (ficha_id,)).fetchone()

    def itens(self, ficha_id, incluir_cancelados=True):
        sql = """
            SELECT i.*, p.nome, i.quantidade * i.preco_unitario AS subtotal
            FROM itens_ficha i JOIN produtos p ON p.id = i.produto_id
            WHERE i.ficha_id = ?
        """
        if not incluir_cancelados:
            sql += " AND i.cancelado = 0"
        sql += " ORDER BY i.id"
        return self.conn.execute(sql, (ficha_id,)).fetchall()

    def total(self, ficha_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(quantidade * preco_unitario), 0) AS t FROM itens_ficha "
            "WHERE ficha_id = ? AND cancelado = 0",
            (ficha_id,),
        ).fetchone()
        return round(row["t"], 2)

    def _exigir_aberta(self, ficha_id):
        ficha = self.obter_ficha(ficha_id)
        if not ficha:
            raise ErroNegocio("Comanda não encontrada.")
        if ficha["status"] != "ABERTA":
            raise ErroNegocio("Esta comanda já foi fechada.")
        return ficha

    def verificar_estoque(self, produto_id, quantidade):
        """Retorna mensagem de alerta se faltar estoque, ou None."""
        disp = self.estoque_disponivel(produto_id)
        if quantidade > disp:
            nome = self.obter_produto(produto_id)["nome"]
            return (
                f"Estoque insuficiente de '{nome}'.\n"
                f"Disponível: {max(disp, 0)} (já descontando outras comandas abertas).\n\n"
                "Lançar mesmo assim?"
            )
        return None

    def lancar_item(self, ficha_id, produto_id, quantidade=1):
        self._exigir_aberta(ficha_id)
        quantidade = int(quantidade)
        if quantidade <= 0:
            raise ErroNegocio("A quantidade deve ser maior que zero.")
        produto = self.obter_produto(produto_id)
        if not produto or not produto["ativo"]:
            raise ErroNegocio("Produto não encontrado ou inativo.")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO itens_ficha (ficha_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (ficha_id, produto_id, quantidade, produto["preco"]),
            )
            return cur.lastrowid

    def cancelar_item(self, item_id):
        item = self.conn.execute("SELECT * FROM itens_ficha WHERE id = ?", (item_id,)).fetchone()
        if not item:
            raise ErroNegocio("Item não encontrado.")
        self._exigir_aberta(item["ficha_id"])
        if item["cancelado"]:
            raise ErroNegocio("Este item já está cancelado.")
        with self.conn:
            self.conn.execute("UPDATE itens_ficha SET cancelado = 1 WHERE id = ?", (item_id,))

    def fechar_ficha(self, ficha_id):
        self._exigir_aberta(ficha_id)
        itens = self.itens(ficha_id, incluir_cancelados=False)
        if not itens:
            raise ErroNegocio("A comanda está vazia. Lance itens ou exclua a comanda.")
        total = self.total(ficha_id)
        with self.conn:  # transação única: baixa estoque + fecha
            for item in itens:
                self.conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
            self.conn.execute(
                "UPDATE fichas SET status = 'FECHADA', total = ?, "
                "fechada_em = datetime('now', 'localtime') WHERE id = ?",
                (total, ficha_id),
            )
        return total

    def excluir_ficha_vazia(self, ficha_id):
        self._exigir_aberta(ficha_id)
        if self.itens(ficha_id, incluir_cancelados=False):
            raise ErroNegocio("Só é possível excluir comandas sem itens. Cancele os itens antes.")
        with self.conn:
            self.conn.execute("DELETE FROM itens_ficha WHERE ficha_id = ?", (ficha_id,))
            self.conn.execute("DELETE FROM fichas WHERE id = ?", (ficha_id,))

    # ------------------------------------------------------------ relatório
    def relatorio_dia(self, dia=None):
        dia = dia or date.today().isoformat()
        resumo = self.conn.execute(
            "SELECT COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total FROM fichas "
            "WHERE status = 'FECHADA' AND date(fechada_em) = ?",
            (dia,),
        ).fetchone()
        produtos = self.conn.execute(
            """
            SELECT p.nome, SUM(i.quantidade) AS qtd, SUM(i.quantidade * i.preco_unitario) AS valor
            FROM itens_ficha i
            JOIN fichas f ON f.id = i.ficha_id
            JOIN produtos p ON p.id = i.produto_id
            WHERE f.status = 'FECHADA' AND i.cancelado = 0 AND date(f.fechada_em) = ?
            GROUP BY p.id ORDER BY qtd DESC, valor DESC
            """,
            (dia,),
        ).fetchall()
        fichas = self.conn.execute(
            "SELECT numero, cliente, aberta_em, fechada_em, total FROM fichas "
            "WHERE status = 'FECHADA' AND date(fechada_em) = ? ORDER BY fechada_em DESC",
            (dia,),
        ).fetchall()
        qtd = resumo["qtd"]
        total = round(resumo["total"], 2)
        return {
            "dia": dia,
            "qtd_fichas": qtd,
            "total": total,
            "ticket_medio": round(total / qtd, 2) if qtd else 0.0,
            "produtos": produtos,
            "fichas": fichas,
        }
