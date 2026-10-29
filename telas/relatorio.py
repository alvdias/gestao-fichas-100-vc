"""Relatório de vendas do dia."""
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

from services import moeda
from telas.estilo import COR_FUNDO, COR_NEUTRA, COR_PAINEL, COR_PRIMARIA, COR_SUAVE, COR_SUCESSO, FONTE, botao, tabela


class TelaRelatorio(ttk.Frame):
    def __init__(self, pai, sistema):
        super().__init__(pai)
        self.sistema = sistema
        self.dia = date.today()
        self._montar()

    def _montar(self):
        self.columnconfigure((0, 1), weight=1, uniform="r")
        self.rowconfigure(2, weight=1)

        topo = ttk.Frame(self)
        topo.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6))
        ttk.Label(topo, text="Vendas do dia", font=(FONTE, 15, "bold")).pack(side="left")
        botao(topo, "▶", lambda: self._mudar_dia(1), COR_NEUTRA).pack(side="right")
        botao(topo, "Hoje", self._hoje, COR_PRIMARIA).pack(side="right", padx=4)
        self.var_data = tk.StringVar()
        ent = ttk.Entry(topo, textvariable=self.var_data, width=12, justify="center", font=(FONTE, 12))
        ent.pack(side="right", padx=4)
        ent.bind("<Return>", lambda e: self._ir_para_data())
        botao(topo, "◀", lambda: self._mudar_dia(-1), COR_NEUTRA).pack(side="right")

        # indicadores
        kpis = ttk.Frame(self)
        kpis.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=6)
        kpis.columnconfigure((0, 1, 2), weight=1, uniform="k")
        self.kpi_total = self._kpi(kpis, 0, "Total vendido", COR_SUCESSO)
        self.kpi_qtd = self._kpi(kpis, 1, "Comandas fechadas", COR_PRIMARIA)
        self.kpi_ticket = self._kpi(kpis, 2, "Ticket médio por comanda", COR_PRIMARIA)

        # tabelas
        esq = tk.Frame(self, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de")
        esq.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(6, 12))
        ttk.Label(esq, text="Produtos mais vendidos", style="Painel.TLabel",
                  font=(FONTE, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        q, self.tv_prod = tabela(esq, [("nome", "Produto", 220, "w"), ("qtd", "Qtd", 70, "center"),
                                       ("valor", "Valor", 110, "e")], altura=8)
        q.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        dir_ = tk.Frame(self, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de")
        dir_.grid(row=2, column=1, sticky="nsew", padx=(6, 12), pady=(6, 12))
        ttk.Label(dir_, text="Comandas fechadas", style="Painel.TLabel",
                  font=(FONTE, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        q, self.tv_fichas = tabela(dir_, [("num", "Nº", 60, "center"), ("cli", "Cliente", 150, "w"),
                                          ("abriu", "Abriu", 70, "center"), ("fechou", "Fechou", 70, "center"),
                                          ("total", "Total", 110, "e")], altura=8)
        q.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _kpi(self, pai, col, titulo, cor):
        card = tk.Frame(pai, bg=COR_PAINEL, highlightthickness=1, highlightbackground="#d0d7de", padx=16, pady=10)
        card.grid(row=0, column=col, sticky="ew", padx=4)
        tk.Label(card, text=titulo, bg=COR_PAINEL, fg=COR_SUAVE, font=(FONTE, 10)).pack(anchor="w")
        valor = tk.Label(card, text="—", bg=COR_PAINEL, fg=cor, font=(FONTE, 22, "bold"))
        valor.pack(anchor="w")
        return valor

    # ------------------------------------------------------------ dados
    def atualizar(self):
        self.var_data.set(self.dia.strftime("%d/%m/%Y"))
        r = self.sistema.relatorio_dia(self.dia.isoformat())
        self.kpi_total.config(text=moeda(r["total"]))
        self.kpi_qtd.config(text=str(r["qtd_fichas"]))
        self.kpi_ticket.config(text=moeda(r["ticket_medio"]))
        self.tv_prod.delete(*self.tv_prod.get_children())
        for p in r["produtos"]:
            self.tv_prod.insert("", "end", values=(p["nome"], p["qtd"], moeda(p["valor"])))
        self.tv_fichas.delete(*self.tv_fichas.get_children())
        for f in r["fichas"]:
            self.tv_fichas.insert("", "end", values=(f["numero"], f["cliente"] or "—", f["aberta_em"][11:16],
                                                     f["fechada_em"][11:16], moeda(f["total"])))

    def _mudar_dia(self, delta):
        self.dia += timedelta(days=delta)
        self.atualizar()

    def _hoje(self):
        self.dia = date.today()
        self.atualizar()

    def _ir_para_data(self):
        try:
            self.dia = datetime.strptime(self.var_data.get().strip(), "%d/%m/%Y").date()
        except ValueError:
            messagebox.showwarning("Data", "Use o formato dd/mm/aaaa, por exemplo 22/10/2026.", parent=self)
            return
        self.atualizar()
