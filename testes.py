"""Testes das regras de negócio. Rodar com: python testes.py"""
import sqlite3
import unittest

import database
from services import ErroNegocio, Sistema, ler_valor, moeda


class TestesSistema(unittest.TestCase):
    def setUp(self):
        self.s = Sistema(database.conectar(":memory:"))
        self.cerveja = self.s.salvar_produto("Cerveja", "Cervejas", 7.0, 10)
        self.porcao = self.s.salvar_produto("Porção", "Porções", 32.5, 3)

    def test_formatos(self):
        self.assertEqual(moeda(1234.5), "R$ 1.234,50")
        self.assertEqual(ler_valor("12,50"), 12.5)
        self.assertEqual(ler_valor("R$ 1.234,50"), 1234.5)
        self.assertEqual(ler_valor("7.5"), 7.5)
        with self.assertRaises(ErroNegocio):
            ler_valor("abc")

    def test_total_e_fechamento(self):
        f = self.s.abrir_ficha("12", "João")
        self.s.lancar_item(f, self.cerveja, 3)
        item = self.s.lancar_item(f, self.porcao, 1)
        self.assertEqual(self.s.total(f), 53.5)
        self.s.cancelar_item(item)
        self.assertEqual(self.s.total(f), 21.0)
        # estoque só baixa no fechamento
        self.assertEqual(self.s.obter_produto(self.cerveja)["estoque"], 10)
        self.assertEqual(self.s.estoque_disponivel(self.cerveja), 7)
        self.assertEqual(self.s.fechar_ficha(f), 21.0)
        self.assertEqual(self.s.obter_produto(self.cerveja)["estoque"], 7)
        self.assertEqual(self.s.obter_produto(self.porcao)["estoque"], 3)  # item cancelado não baixa
        with self.assertRaises(ErroNegocio):
            self.s.lancar_item(f, self.cerveja, 1)

    def test_preco_congelado_no_lancamento(self):
        f = self.s.abrir_ficha("1")
        self.s.lancar_item(f, self.cerveja, 2)
        self.s.salvar_produto("Cerveja", "Cervejas", 9.0, 10, self.cerveja)
        self.assertEqual(self.s.total(f), 14.0)

    def test_alerta_estoque(self):
        f = self.s.abrir_ficha("1")
        self.s.lancar_item(f, self.porcao, 2)
        self.assertIsNone(self.s.verificar_estoque(self.porcao, 1))
        self.assertIsNotNone(self.s.verificar_estoque(self.porcao, 2))

    def test_validacoes(self):
        self.s.abrir_ficha("5")
        with self.assertRaises(ErroNegocio):
            self.s.abrir_ficha("5")  # número repetido entre abertas
        with self.assertRaises(ErroNegocio):
            self.s.salvar_produto("cerveja", "", 1, 0)  # nome repetido
        vazia = self.s.abrir_ficha("6")
        with self.assertRaises(ErroNegocio):
            self.s.fechar_ficha(vazia)
        self.s.excluir_ficha_vazia(vazia)
        self.assertIsNone(self.s.obter_ficha(vazia))

    def test_relatorio(self):
        for n in ("1", "2"):
            f = self.s.abrir_ficha(n)
            self.s.lancar_item(f, self.cerveja, 2)
            self.s.fechar_ficha(f)
        r = self.s.relatorio_dia()
        self.assertEqual(r["qtd_fichas"], 2)
        self.assertEqual(r["total"], 28.0)
        self.assertEqual(r["ticket_medio"], 14.0)
        self.assertEqual(r["produtos"][0]["qtd"], 4)

    def test_exemplos(self):
        s = Sistema(database.conectar(":memory:"))
        self.assertFalse(s.tem_produtos())
        s.carregar_exemplos()
        self.assertTrue(len(s.listar_produtos()) > 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
