"""Tela principal: comandas abertas, lançamento de itens e fechamento."""
import tkinter as tk
from tkinter import messagebox, ttk

from services import ErroNegocio, ler_valor, moeda
from telas.estilo import (
    COR_CARD, COR_CARD_SEL, COR_FUNDO, COR_NEUTRA, COR_PAINEL, COR_PERIGO,
    COR_PRIMARIA, COR_SUAVE, COR_SUCESSO, COR_TEXTO, FONTE, AreaRolavel, botao, tabela,
)


class TelaComandas(ttk.Frame):
    def __init__(self, pai, sistema, ao_mudar=None):
        super().__init__(pai)
        self.sistema = sistema
        self.ao_mudar = ao_mudar or (lambda: None)
        self.ficha_id = None
        self.categoria = None
        self._montar()
        self.atualizar()

    # ================================================================ layout
    def _montar(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ---------- coluna esquerda: comandas abertas
        esquerda = ttk.Frame(self, width=330)
        esquerda.grid(row=0, column=0, sticky="nsw", padx=(12, 6), pady=12)
        esquerda.grid_propagate(False)
        esquerda.rowconfigure(2, weight=1)
        esquerda.columnconfigure(0, weight=1)

        topo = ttk.Frame(esquerda)
        topo.grid(row=0, column=0, sticky="ew")
        ttk.Label(topo, text="Comandas abertas", font=(FONTE, 15, "bold")).pack(side="left")
        self.lbl_qtd_abertas = ttk.Label(topo, text="", foreground=COR_SUAVE)
        self.lbl_qtd_abertas.pack(side="right")

        botao(esquerda, "+  Nova comanda  (F2)", self.nova_comanda, COR_PRIMARIA, grande=True).grid(
            row=1, column=0, sticky="ew", pady=(8, 8))

        self.area_cards = AreaRolavel(esquerda)
        self.area_cards.grid(row=2, column=0, sticky="nsew")

        # ---------- coluna direita: detalhe da comanda
        self.direita = tk.Frame(self, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de")
        self.direita.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        self.vazio = tk.Label(
            self.direita, bg=COR_PAINEL, fg=COR_SUAVE, font=(FONTE, 14),
            text="Selecione uma comanda à esquerda\nou clique em  “+ Nova comanda”.",
        )
        self.detalhe = ttk.Frame(self.direita, style="Painel.TFrame")
        self._montar_detalhe(self.detalhe)

    def _montar_detalhe(self, d):
        d.columnconfigure(0, weight=3, uniform="col")
        d.columnconfigure(1, weight=4, uniform="col")
        d.rowconfigure(1, weight=1)

        # cabeçalho
        cab = ttk.Frame(d, style="Painel.TFrame")
        cab.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 6))
        self.lbl_titulo = ttk.Label(cab, text="", style="Titulo.TLabel")
        self.lbl_titulo.pack(side="left")
        self.lbl_sub = ttk.Label(cab, text="", style="Sub.TLabel")
        self.lbl_sub.pack(side="left", padx=12, pady=(6, 0))
        botao(cab, "Excluir comanda vazia", self.excluir_comanda, COR_NEUTRA).pack(side="right")

        # ---------- produtos (esquerda do detalhe)
        prod = ttk.Frame(d, style="Painel.TFrame")
        prod.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=4)
        prod.rowconfigure(3, weight=1)
        prod.columnconfigure(0, weight=1)

        ttk.Label(prod, text="Adicionar produto", style="Painel.TLabel",
                  font=(FONTE, 12, "bold")).grid(row=0, column=0, sticky="w")
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *a: self._carregar_produtos())
        self.ent_busca = ttk.Entry(prod, textvariable=self.var_busca, font=(FONTE, 12))
        self.ent_busca.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        self.ent_busca.bind("<Return>", lambda e: self.lancar())
        self.ent_busca.bind("<Down>", self._focar_lista_produtos)

        self.quadro_cats = tk.Frame(prod, bg=COR_PAINEL)
        self.quadro_cats.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        quadro, self.tv_prod = tabela(prod, [
            ("nome", "Produto", 180, "w"),
            ("preco", "Preço", 90, "e"),
            ("disp", "Disp.", 60, "center"),
        ], altura=8)
        quadro.grid(row=3, column=0, sticky="nsew")
        self.tv_prod.tag_configure("baixo", foreground=COR_PERIGO)
        self.tv_prod.bind("<Double-1>", lambda e: self.lancar(1))
        self.tv_prod.bind("<Return>", lambda e: self.lancar())

        qtd = ttk.Frame(prod, style="Painel.TFrame")
        qtd.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(qtd, text="Qtd:", style="Painel.TLabel", font=(FONTE, 12)).pack(side="left")
        botao(qtd, "−", lambda: self._mudar_qtd(-1), COR_NEUTRA).pack(side="left", padx=(6, 2))
        self.var_qtd = tk.StringVar(value="1")
        ent_qtd = ttk.Entry(qtd, textvariable=self.var_qtd, width=4, justify="center", font=(FONTE, 13, "bold"))
        ent_qtd.pack(side="left")
        ent_qtd.bind("<Return>", lambda e: self.lancar())
        botao(qtd, "+", lambda: self._mudar_qtd(1), COR_NEUTRA).pack(side="left", padx=(2, 10))
        botao(qtd, "Lançar  (Enter)", self.lancar, COR_PRIMARIA, grande=True).pack(
            side="left", fill="x", expand=True)
        ttk.Label(prod, text="Dica: digite parte do nome e tecle Enter. Duplo clique lança 1 unidade.",
                  style="Sub.TLabel", wraplength=320).grid(row=5, column=0, sticky="w", pady=(6, 0))

        # ---------- itens (direita do detalhe)
        itens = ttk.Frame(d, style="Painel.TFrame")
        itens.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=4)
        itens.rowconfigure(1, weight=1)
        itens.columnconfigure(0, weight=1)
        ttk.Label(itens, text="Itens da comanda", style="Painel.TLabel",
                  font=(FONTE, 12, "bold")).grid(row=0, column=0, sticky="w")
        quadro, self.tv_itens = tabela(itens, [
            ("hora", "Hora", 60, "center"),
            ("qtd", "Qtd", 50, "center"),
            ("produto", "Produto", 200, "w"),
            ("unit", "Unit.", 90, "e"),
            ("sub", "Subtotal", 100, "e"),
        ], altura=8)
        quadro.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.tv_itens.tag_configure("cancelado", foreground="#9aa0a6", font=(FONTE, 10, "overstrike"))
        self.tv_itens.bind("<Delete>", lambda e: self.cancelar_item())
        botao(itens, "Cancelar item selecionado  (Del)", self.cancelar_item, COR_PERIGO).grid(
            row=2, column=0, sticky="w", pady=(8, 0))

        # ---------- rodapé: total e fechamento
        rod = tk.Frame(d, bg="#f6f8fa")
        rod.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(12, 0))
        tk.Label(rod, text="TOTAL", bg="#f6f8fa", fg=COR_SUAVE, font=(FONTE, 12, "bold")).pack(
            side="left", padx=(16, 8), pady=12)
        self.lbl_total = tk.Label(rod, text=moeda(0), bg="#f6f8fa", fg=COR_SUCESSO, font=(FONTE, 28, "bold"))
        self.lbl_total.pack(side="left")

        div = tk.Frame(rod, bg="#f6f8fa")
        div.pack(side="left", padx=28)
        tk.Label(div, text="Dividir por", bg="#f6f8fa", fg=COR_SUAVE, font=(FONTE, 10)).pack(anchor="w")
        linha = tk.Frame(div, bg="#f6f8fa")
        linha.pack(anchor="w")
        self.var_pessoas = tk.StringVar(value="1")
        sp = ttk.Spinbox(linha, from_=1, to=50, width=4, textvariable=self.var_pessoas,
                         command=self._atualizar_divisao, font=(FONTE, 11))
        sp.pack(side="left")
        sp.bind("<KeyRelease>", lambda e: self._atualizar_divisao())
        self.lbl_por_pessoa = tk.Label(linha, text="", bg="#f6f8fa", fg=COR_TEXTO, font=(FONTE, 11, "bold"))
        self.lbl_por_pessoa.pack(side="left", padx=8)

        botao(rod, "Fechar comanda  (F9)", self.fechar_comanda, COR_SUCESSO, grande=True).pack(
            side="right", padx=16, pady=10)

    # ================================================================ dados
    def atualizar(self):
        """Recarrega cards e detalhe (chamado ao trocar de aba também)."""
        self._carregar_cards()
        self._carregar_categorias()
        self._mostrar_detalhe()

    def _carregar_cards(self):
        for w in self.area_cards.interno.winfo_children():
            w.destroy()
        abertas = self.sistema.fichas_abertas()
        self.lbl_qtd_abertas.config(text=f"{len(abertas)} aberta(s)")
        if self.ficha_id and not any(f["id"] == self.ficha_id for f in abertas):
            self.ficha_id = None
        if not abertas:
            tk.Label(self.area_cards.interno, text="Nenhuma comanda aberta.", bg=COR_FUNDO,
                     fg=COR_SUAVE, font=(FONTE, 11)).pack(pady=20)
            return
        grade = self.area_cards.interno
        for c in range(2):
            grade.columnconfigure(c, weight=1, uniform="card")
        for i, f in enumerate(abertas):
            self._card(grade, f).grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)

    def _card(self, pai, f):
        sel = f["id"] == self.ficha_id
        bg = COR_CARD_SEL if sel else COR_CARD
        fg = "white" if sel else COR_TEXTO
        fg2 = "#dbe7ff" if sel else COR_SUAVE
        card = tk.Frame(pai, bg=bg, cursor="hand2", padx=10, pady=8)
        tk.Label(card, text=f"Nº {f['numero']}", bg=bg, fg=fg, font=(FONTE, 16, "bold")).pack(anchor="w")
        tk.Label(card, text=f["cliente"] or "—", bg=bg, fg=fg2, font=(FONTE, 10)).pack(anchor="w")
        tk.Label(card, text=moeda(f["parcial"]), bg=bg, fg=fg, font=(FONTE, 13, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(card, text=f"{f['qtd_itens']} itens · {f['aberta_em'][11:16]}",
                 bg=bg, fg=fg2, font=(FONTE, 9)).pack(anchor="w")
        for w in [card, *card.winfo_children()]:
            w.bind("<Button-1>", lambda e, fid=f["id"]: self.selecionar(fid))
        return card

    def _carregar_categorias(self):
        for w in self.quadro_cats.winfo_children():
            w.destroy()
        cats = ["Todas", *self.sistema.categorias()]
        if self.categoria not in cats:
            self.categoria = None
        for i, cat in enumerate(cats):
            ativa = (cat == "Todas" and self.categoria is None) or cat == self.categoria
            b = tk.Button(
                self.quadro_cats, text=cat, relief="flat", cursor="hand2", bd=0,
                bg=COR_PRIMARIA if ativa else "#eef1f4", fg="white" if ativa else COR_TEXTO,
                font=(FONTE, 10, "bold" if ativa else "normal"), padx=10, pady=4,
                command=lambda c=cat: self._filtrar_categoria(c),
            )
            b.grid(row=i // 4, column=i % 4, sticky="ew", padx=2, pady=2)

    def _filtrar_categoria(self, cat):
        self.categoria = None if cat == "Todas" else cat
        self._carregar_categorias()
        self._carregar_produtos()

    def _carregar_produtos(self):
        self.tv_prod.delete(*self.tv_prod.get_children())
        for p in self.sistema.listar_produtos(self.var_busca.get()):
            if self.categoria and p["categoria"] != self.categoria:
                continue
            disp = self.sistema.estoque_disponivel(p["id"])
            tags = ("baixo",) if disp <= 5 else ()
            self.tv_prod.insert("", "end", iid=str(p["id"]), tags=tags,
                                values=(p["nome"], moeda(p["preco"]), disp))
        filhos = self.tv_prod.get_children()
        if filhos:
            self.tv_prod.selection_set(filhos[0])
            self.tv_prod.focus(filhos[0])

    def _mostrar_detalhe(self):
        if not self.ficha_id:
            self.detalhe.pack_forget()
            self.vazio.pack(expand=True)
            return
        self.vazio.pack_forget()
        self.detalhe.pack(fill="both", expand=True)
        f = self.sistema.obter_ficha(self.ficha_id)
        self.lbl_titulo.config(text=f"Comanda Nº {f['numero']}")
        cliente = f" · {f['cliente']}" if f["cliente"] else ""
        self.lbl_sub.config(text=f"Aberta às {f['aberta_em'][11:16]}{cliente}")

        self.tv_itens.delete(*self.tv_itens.get_children())
        for it in self.sistema.itens(self.ficha_id):
            nome = it["nome"] + ("  (cancelado)" if it["cancelado"] else "")
            self.tv_itens.insert("", "end", iid=str(it["id"]),
                                 tags=("cancelado",) if it["cancelado"] else (),
                                 values=(it["lancado_em"][11:16], it["quantidade"], nome,
                                         moeda(it["preco_unitario"]), moeda(it["subtotal"])))
        filhos = self.tv_itens.get_children()
        if filhos:
            self.tv_itens.see(filhos[-1])
        self.lbl_total.config(text=moeda(self.sistema.total(self.ficha_id)))
        self._atualizar_divisao()
        self._carregar_produtos()

    def _atualizar_divisao(self):
        if not self.ficha_id:
            return
        try:
            n = max(1, int(self.var_pessoas.get()))
        except ValueError:
            n = 1
        total = self.sistema.total(self.ficha_id)
        self.lbl_por_pessoa.config(text=f"= {moeda(total / n)} por pessoa" if n > 1 else "")

    # ================================================================ ações
    def selecionar(self, ficha_id):
        self.ficha_id = ficha_id
        self.var_busca.set("")
        self.var_qtd.set("1")
        self.var_pessoas.set("1")
        self._carregar_cards()
        self._mostrar_detalhe()
        self.ent_busca.focus_set()

    def nova_comanda(self):
        dlg = DialogoNovaComanda(self.winfo_toplevel(), self._sugerir_numero())
        if not dlg.resultado:
            return
        numero, cliente = dlg.resultado
        try:
            fid = self.sistema.abrir_ficha(numero, cliente)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.ao_mudar()
        self.selecionar(fid)

    def _sugerir_numero(self):
        usados = {f["numero"] for f in self.sistema.fichas_abertas()}
        n = 1
        while str(n) in usados:
            n += 1
        return str(n)

    def _mudar_qtd(self, delta):
        try:
            q = int(self.var_qtd.get())
        except ValueError:
            q = 1
        self.var_qtd.set(str(max(1, q + delta)))

    def _focar_lista_produtos(self, _evento=None):
        self.tv_prod.focus_set()
        return "break"

    def lancar(self, quantidade=None):
        if not self.ficha_id:
            return
        sel = self.tv_prod.selection()
        if not sel:
            messagebox.showinfo("Lançar", "Escolha um produto na lista.", parent=self)
            return
        produto_id = int(sel[0])
        if quantidade is None:
            try:
                quantidade = int(self.var_qtd.get())
            except ValueError:
                messagebox.showwarning("Atenção", "Quantidade inválida.", parent=self)
                return
        alerta = self.sistema.verificar_estoque(produto_id, quantidade)
        if alerta and not messagebox.askyesno("Estoque baixo", alerta, parent=self):
            return
        try:
            self.sistema.lancar_item(self.ficha_id, produto_id, quantidade)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.var_busca.set("")
        self.var_qtd.set("1")
        self._carregar_cards()
        self._mostrar_detalhe()
        self.ent_busca.focus_set()

    def cancelar_item(self):
        sel = self.tv_itens.selection()
        if not sel:
            messagebox.showinfo("Cancelar item", "Selecione o item na lista de itens.", parent=self)
            return
        valores = self.tv_itens.item(sel[0], "values")
        if not messagebox.askyesno("Cancelar item", f"Cancelar {valores[1]}x {valores[2]}?", parent=self):
            return
        try:
            self.sistema.cancelar_item(int(sel[0]))
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self._carregar_cards()
        self._mostrar_detalhe()

    def excluir_comanda(self):
        if not self.ficha_id:
            return
        f = self.sistema.obter_ficha(self.ficha_id)
        if not messagebox.askyesno("Excluir", f"Excluir a comanda Nº {f['numero']}?", parent=self):
            return
        try:
            self.sistema.excluir_ficha_vazia(self.ficha_id)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.ficha_id = None
        self.atualizar()
        self.ao_mudar()

    def fechar_comanda(self):
        if not self.ficha_id:
            return
        f = self.sistema.obter_ficha(self.ficha_id)
        if not self.sistema.itens(self.ficha_id, incluir_cancelados=False):
            messagebox.showwarning("Atenção", "A comanda está vazia. Lance itens ou exclua a comanda.", parent=self)
            return
        total = self.sistema.total(self.ficha_id)
        dlg = DialogoFechamento(self.winfo_toplevel(), f["numero"], total)
        if not dlg.confirmado:
            return
        try:
            self.sistema.fechar_ficha(self.ficha_id)
        except ErroNegocio as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        self.ficha_id = None
        self.atualizar()
        self.ao_mudar()

    # atalhos chamados pela janela principal
    def atalho_fechar(self):
        if self.ficha_id:
            self.fechar_comanda()

    def atalho_busca(self):
        if self.ficha_id:
            self.ent_busca.focus_set()


# ==================================================================== diálogos
class _Dialogo(tk.Toplevel):
    def __init__(self, pai, titulo):
        super().__init__(pai)
        self.title(titulo)
        self.configure(bg=COR_PAINEL, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(pai)
        self.bind("<Escape>", lambda e: self.destroy())

    def _mostrar(self, foco):
        self.update_idletasks()
        pai = self.master
        x = pai.winfo_rootx() + (pai.winfo_width() - self.winfo_width()) // 2
        y = pai.winfo_rooty() + (pai.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.grab_set()
        foco.focus_set()
        self.wait_window()


class DialogoNovaComanda(_Dialogo):
    def __init__(self, pai, sugestao):
        super().__init__(pai, "Nova comanda")
        self.resultado = None
        tk.Label(self, text="Número da comanda / mesa", bg=COR_PAINEL, font=(FONTE, 11)).pack(anchor="w")
        self.var_num = tk.StringVar(value=sugestao)
        e1 = ttk.Entry(self, textvariable=self.var_num, font=(FONTE, 16, "bold"), width=18)
        e1.pack(fill="x", pady=(4, 12))
        e1.select_range(0, "end")
        tk.Label(self, text="Nome do cliente (opcional)", bg=COR_PAINEL, font=(FONTE, 11)).pack(anchor="w")
        self.var_cli = tk.StringVar()
        e2 = ttk.Entry(self, textvariable=self.var_cli, font=(FONTE, 12))
        e2.pack(fill="x", pady=(4, 16))
        botoes = tk.Frame(self, bg=COR_PAINEL)
        botoes.pack(fill="x")
        botao(botoes, "Abrir comanda", self._ok, COR_SUCESSO, grande=True).pack(side="right")
        botao(botoes, "Cancelar", self.destroy, COR_NEUTRA, grande=True).pack(side="right", padx=8)
        e1.bind("<Return>", lambda e: e2.focus_set())
        e2.bind("<Return>", lambda e: self._ok())
        self._mostrar(e1)

    def _ok(self):
        self.resultado = (self.var_num.get(), self.var_cli.get())
        self.destroy()


class DialogoFechamento(_Dialogo):
    def __init__(self, pai, numero, total):
        super().__init__(pai, f"Fechar comanda Nº {numero}")
        self.confirmado = False
        self.total = total
        tk.Label(self, text=f"Comanda Nº {numero}", bg=COR_PAINEL, font=(FONTE, 13)).pack(anchor="w")
        tk.Label(self, text="Total a pagar", bg=COR_PAINEL, fg=COR_SUAVE, font=(FONTE, 11)).pack(anchor="w", pady=(10, 0))
        tk.Label(self, text=moeda(total), bg=COR_PAINEL, fg=COR_SUCESSO, font=(FONTE, 30, "bold")).pack(anchor="w")

        tk.Label(self, text="Valor recebido (opcional, para calcular o troco)", bg=COR_PAINEL,
                 font=(FONTE, 10)).pack(anchor="w", pady=(14, 0))
        self.var_receb = tk.StringVar()
        self.var_receb.trace_add("write", lambda *a: self._troco())
        e = ttk.Entry(self, textvariable=self.var_receb, font=(FONTE, 14), width=16)
        e.pack(anchor="w", pady=4)
        self.lbl_troco = tk.Label(self, text="", bg=COR_PAINEL, font=(FONTE, 13, "bold"))
        self.lbl_troco.pack(anchor="w")

        tk.Label(self, text="O estoque será baixado ao confirmar.", bg=COR_PAINEL, fg=COR_SUAVE,
                 font=(FONTE, 9)).pack(anchor="w", pady=(12, 8))
        botoes = tk.Frame(self, bg=COR_PAINEL)
        botoes.pack(fill="x")
        botao(botoes, "Confirmar fechamento", self._ok, COR_SUCESSO, grande=True).pack(side="right")
        botao(botoes, "Voltar", self.destroy, COR_NEUTRA, grande=True).pack(side="right", padx=8)
        e.bind("<Return>", lambda ev: self._ok())
        self._mostrar(e)

    def _troco(self):
        txt = self.var_receb.get().strip()
        if not txt:
            self.lbl_troco.config(text="")
            return
        try:
            recebido = ler_valor(txt)
        except ErroNegocio:
            self.lbl_troco.config(text="Valor inválido", fg=COR_PERIGO)
            return
        dif = round(recebido - self.total, 2)
        if dif >= 0:
            self.lbl_troco.config(text=f"Troco: {moeda(dif)}", fg=COR_PRIMARIA)
        else:
            self.lbl_troco.config(text=f"Faltam: {moeda(-dif)}", fg=COR_PERIGO)

    def _ok(self):
        self.confirmado = True
        self.destroy()
