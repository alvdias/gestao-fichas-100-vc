"""Gestão de Comandas para bares — janela principal."""
import sys
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

import database
from services import Sistema
from telas.comandas import TelaComandas
from telas.estilo import COR_SUAVE, FONTE, aplicar_estilo
from telas.produtos import TelaProdutos
from telas.relatorio import TelaRelatorio

VERSAO = "1.0"


def ativar_alta_resolucao():
    """Deixa letras nítidas em telas com escala 125%/150% do Windows 11."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Comandas")
        self.minsize(1100, 680)
        try:
            self.state("zoomed")  # abre maximizado no Windows
        except tk.TclError:
            self.geometry("1280x760")
        aplicar_estilo(self)
        self.report_callback_exception = self._erro_inesperado

        self.conn = database.conectar()
        self.sistema = Sistema(self.conn)

        rodape = ttk.Frame(self)
        rodape.pack(side="bottom", fill="x", padx=12, pady=4)
        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        self.tela_comandas = TelaComandas(self.abas, self.sistema, ao_mudar=self._mudou)
        self.tela_produtos = TelaProdutos(self.abas, self.sistema, ao_mudar=self._mudou)
        self.tela_relatorio = TelaRelatorio(self.abas, self.sistema)
        self.abas.add(self.tela_comandas, text="  Comandas  ")
        self.abas.add(self.tela_produtos, text="  Produtos e estoque  ")
        self.abas.add(self.tela_relatorio, text="  Relatório do dia  ")
        self.abas.bind("<<NotebookTabChanged>>", self._trocou_aba)

        ttk.Label(rodape, foreground=COR_SUAVE, font=(FONTE, 9),
                  text="Atalhos: F2 nova comanda · F9 fechar comanda · Ctrl+F buscar produto · Del cancelar item"
                  ).pack(side="left")
        ttk.Label(rodape, foreground=COR_SUAVE, font=(FONTE, 9),
                  text=f"v{VERSAO} · Dados em: {database.CAMINHO_BANCO}").pack(side="right")

        self.bind_all("<F2>", lambda e: self._atalho_nova())
        self.bind_all("<F9>", lambda e: self._atalho_fechar())
        self.bind_all("<Control-f>", lambda e: self._atalho_busca())
        self.protocol("WM_DELETE_WINDOW", self._sair)

        self.after(200, self._primeira_execucao)

    # ------------------------------------------------------------ eventos
    def _mudou(self):
        """Algo mudou em produtos/comandas: recarrega as outras telas."""
        self.tela_produtos.atualizar()
        self.tela_comandas._carregar_categorias()

    def _trocou_aba(self, _e=None):
        atual = self.abas.nametowidget(self.abas.select())
        atual.atualizar()

    def _atalho_nova(self):
        self.abas.select(self.tela_comandas)
        self.tela_comandas.nova_comanda()

    def _atalho_fechar(self):
        self.abas.select(self.tela_comandas)
        self.tela_comandas.atalho_fechar()

    def _atalho_busca(self):
        self.abas.select(self.tela_comandas)
        self.tela_comandas.atalho_busca()

    def _primeira_execucao(self):
        if self.sistema.tem_produtos():
            return
        if messagebox.askyesno(
            "Bem-vindo!",
            "Nenhum produto cadastrado ainda.\n\n"
            "Quer carregar uma lista de exemplo de bar (cervejas, drinks, porções)?\n"
            "Você pode editar preços e estoques depois na aba “Produtos e estoque”.",
        ):
            self.sistema.carregar_exemplos()
        else:
            self.abas.select(self.tela_produtos)
        self.tela_comandas.atualizar()
        self.tela_produtos.atualizar()

    def _sair(self):
        abertas = len(self.sistema.fichas_abertas())
        if abertas and not messagebox.askyesno(
            "Sair", f"Há {abertas} comanda(s) aberta(s). Elas continuarão salvas.\n\nDeseja sair?"
        ):
            return
        self.conn.close()
        self.destroy()

    def _erro_inesperado(self, tipo, valor, tb):
        detalhe = "".join(traceback.format_exception(tipo, valor, tb))
        try:
            with open(database.CAMINHO_BANCO.replace("fichas.db", "erros.log"), "a", encoding="utf-8") as f:
                f.write(detalhe + "\n")
        except OSError:
            pass
        messagebox.showerror("Erro inesperado",
                             f"Ocorreu um erro, mas seus dados estão salvos.\n\n{valor}")


def main():
    ativar_alta_resolucao()
    App().mainloop()


if __name__ == "__main__":
    main()
