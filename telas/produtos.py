"""Cadastro de produtos e controle de estoque."""
import tkinter as tk
from tkinter import messagebox, ttk

from services import ErroNegocio, ler_valor, moeda
from telas.estilo import (
    COR_NEUTRA, COR_PAINEL, COR_PERIGO, COR_PRIMARIA, COR_SUAVE, COR_SUCESSO, FONTE, botao, tabela,
)

ESTOQUE_BAIXO = 5


class TelaProdutos(ttk.Frame):
    def __init__(self, pai, sistema, ao_mudar=None):
        super().__init__(pai)
        self.sistema = sistema
        self.ao_mudar = ao_mudar or (lambda: None)
        self.produto_id = None
        self._montar()
        self.atualizar()

    def _montar(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ---------- lista
        lista = tk.Frame(self, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de")
        lista.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        lista.columnconfigure(0, weight=1)
        lista.rowconfigure(2, weight=1)

        ttk.Label(lista, text="Produtos", style="Titulo.TLabel").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        filtros = ttk.Frame(lista, style="Painel.TFrame")
        filtros.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        ttk.Label(filtros, text="Buscar:", style="Painel.TLabel").pack(side="left")
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *a: self._carregar())
        ttk.Entry(filtros, textvariable=self.var_busca, width=30).pack(side="left", padx=6)
        self.var_inativos = tk.BooleanVar(value=False)
        tk.Checkbutton(filtros, text="Mostrar desativados", variable=self.var_inativos,
                       bg=COR_PAINEL, font=(FONTE, 10), command=self._carregar).pack(side="left", padx=10)

        quadro, self.tv = tabela(lista, [
            ("nome", "Produto", 240, "w"),
            ("cat", "Categoria", 130, "w"),
            ("preco", "Preço", 100, "e"),
            ("estoque", "Estoque", 80, "center"),
            ("disp", "Disponível*", 95, "center"),
            ("sit", "Situação", 90, "center"),
        ], altura=10)
        quadro.grid(row=2, column=0, sticky="nsew", padx=14)
        self.tv.tag_configure("baixo", foreground=COR_PERIGO)
        self.tv.tag_configure("inativo", foreground="#9aa0a6")
        self.tv.bind("<<TreeviewSelect>>", self._ao_selecionar)
        ttk.Label(lista, style="Sub.TLabel",
                  text=f"* Disponível = estoque menos o que já está lançado em comandas abertas. "
                       f"Em vermelho: {ESTOQUE_BAIXO} ou menos.").grid(row=3, column=0, sticky="w", padx=14, pady=8)

        # ---------- formulário
        form = tk.Frame(self, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de", width=360)
        form.grid(row=0, column=1, sticky="ns", padx=(6, 12), pady=12)
        form.grid_propagate(False)
        form.columnconfigure(0, weight=1)
        p = {"padx": 16, "sticky": "ew"}

        self.lbl_form = ttk.Label(form, text="Novo produto", style="Titulo.TLabel")
        self.lbl_form.grid(row=0, column=0, pady=(12, 10), **p)

        self.var_nome = tk.StringVar()
        self.var_cat = tk.StringVar()
        self.var_preco = tk.StringVar()
        self.var_estoque = tk.StringVar(value="0")

        ttk.Label(form, text="Nome", style="Painel.TLabel").grid(row=1, column=0, **p)
        self.ent_nome = ttk.Entry(form, textvariable=self.var_nome, font=(FONTE, 12))
        self.ent_nome.grid(row=2, column=0, pady=(2, 8), **p)
        ttk.Label(form, text="Categoria (ex.: Cervejas, Drinks, Porções)", style="Painel.TLabel").grid(row=3, column=0, **p)
        self.cmb_cat = ttk.Combobox(form, textvariable=self.var_cat, font=(FONTE, 12))
        self.cmb_cat.grid(row=4, column=0, pady=(2, 8), **p)
        ttk.Label(form, text="Preço de venda (R$)", style="Painel.TLabel").grid(row=5, column=0, **p)
        ttk.Entry(form, textvariable=self.var_preco, font=(FONTE, 12)).grid(row=6, column=0, pady=(2, 8), **p)
        ttk.Label(form, text="Estoque atual", style="Painel.TLabel").grid(row=7, column=0, **p)
        ttk.Entry(form, textvariable=self.var_estoque, font=(FONTE, 12)).grid(row=8, column=0, pady=(2, 12), **p)

        bts = tk.Frame(form, bg=COR_PAINEL)
        bts.grid(row=9, column=0, **p)
        bts.columnconfigure((0, 1), weight=1)
        botao(bts, "Salvar", self.salvar, COR_SUCESSO, grande=True).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        botao(bts, "Novo", self.limpar, COR_PRIMARIA, grande=True).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.bt_ativo = botao(form, "Desativar produto", self.alternar_ativo, COR_NEUTRA)
        self.bt_ativo.grid(row=10, column=0, pady=(8, 0), **p)

        ttk.Separator(form).grid(row=11, column=0, pady=16, **p)
        ttk.Label(form, text="Entrada de mercadoria", style="Painel.TLabel",
                  font=(FONTE, 12, "bold")).grid(row=12, column=0, **p)
        ttk.Label(form, text="Some ao estoque o que chegou do fornecedor.",
                  style="Sub.TLabel").grid(row=13, column=0, **p)
        linha = ttk.Frame(form, style="Painel.TFrame")
        linha.grid(row=14, column=0, pady=6, **p)
        self.var_entrada = tk.StringVar()
        ttk.Entry(linha, textvariable=self.var_entrada, width=8, font=(FONTE, 12)).pack(side="left")
        botao(linha, "Adicionar ao estoque", self.entrada, COR_PRIMARIA).pack(side="left", padx=8, fill="x", expand=True)

        self.ent_nome.bind("<Return>", lambda e: self.salvar())

    # ------------------------------------------------------------ dados
    def atualizar(self):
        self._carregar()
        self.cmb_cat["values"] = self.sistema.categorias()

    def _carregar(self):
        sel = self.produto_id
        self.tv.delete(*self.tv.get_children())
        for p in self.sistema.listar_produtos(self.var_busca.get(), self.var_inativos.get()):
            disp = self.sistema.estoque_disponivel(p["id"])
            tags = ()
            if not p["ativo"]:
                tags = ("inativo",)
            elif disp <= ESTOQUE_BAIXO:
                tags = ("baixo",)
            self.tv.insert("", "end", iid=str(p["id"]), tags=tags, values=(
                p["nome"], p["categoria"], moeda(p["preco"]), p["estoque"], disp,
                "Ativo" if p["ativo"] else "Desativado"))
        if sel and self.tv.exists(str(sel)):
            self.tv.selection_set(str(sel))

    def _ao_selecionar(self, _e=None):
        sel = self.tv.selection()
        if not sel:
            return
        p = self.sistema.obter_produto(int(sel[0]))
        self.produto_id = p["id"]
        self.lbl_form.config(text="Editar produto")
        self.var_nome.set(p["nome"])
        self.var_cat.set(p["categoria"])
        self.var_preco.set(f"{p['preco']:.2f}".replace(".", ","))
        self.var_estoque.set(str(p["estoque"]))
        self.bt_ativo.config(text="Desativar produto" if p["ativo"] else "Reativar produto")

    def limpar(self):
        self.produto_id = None
        self.tv.selection_remove(*self.tv.selection())
        self.lbl_form.config(text="Novo produto")
        for v in (self.var_nome, self.var_cat, self.var_preco, self.var_entrada):
            v.set("")
        self.var_estoque.set("0")
        self.bt_ativo.config(text="Desativar produto")
        self.ent_nome.focus_set()

    # ------------------------------------------------------------ ações
    def salvar(self):
        try:
            preco = ler_valor(self.var_preco.get())
            try:
                estoque = int(self.var_estoque.get() or 0)
            except ValueError:
                raise ErroNegocio("Estoque deve ser um número inteiro.")
            self.produto_id = self.sistema.salvar_produto(
                self.var_nome.get(), self.var_cat.get(), preco, estoque, self.produto_id)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.atualizar()
        self.ao_mudar()
        self.limpar()

    def alternar_ativo(self):
        if not self.produto_id:
            messagebox.showinfo("Produtos", "Selecione um produto na lista.", parent=self)
            return
        self.sistema.alternar_ativo(self.produto_id)
        self.atualizar()
        self.ao_mudar()
        self._ao_selecionar()

    def entrada(self):
        if not self.produto_id:
            messagebox.showinfo("Produtos", "Selecione um produto na lista.", parent=self)
            return
        try:
            try:
                qtd = int(self.var_entrada.get())
            except ValueError:
                raise ErroNegocio("Informe uma quantidade inteira (ex.: 24).")
            self.sistema.entrada_estoque(self.produto_id, qtd)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.var_entrada.set("")
        self.atualizar()
        self.ao_mudar()
        self._ao_selecionar()
