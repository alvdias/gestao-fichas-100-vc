"""Cores, fontes e componentes visuais compartilhados."""
import tkinter as tk
from tkinter import ttk

FONTE = "Segoe UI"

COR_FUNDO = "#f4f5f7"
COR_PAINEL = "#ffffff"
COR_PRIMARIA = "#1f6feb"
COR_SUCESSO = "#1a7f37"
COR_PERIGO = "#cf222e"
COR_NEUTRA = "#57606a"
COR_TEXTO = "#1f2328"
COR_SUAVE = "#656d76"
COR_ALERTA_FUNDO = "#fff1f0"
COR_CARD = "#eaf2ff"
COR_CARD_SEL = "#1f6feb"


def aplicar_estilo(root):
    root.configure(bg=COR_FUNDO)
    estilo = ttk.Style(root)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass
    estilo.configure(".", font=(FONTE, 11), background=COR_FUNDO, foreground=COR_TEXTO)
    estilo.configure("TFrame", background=COR_FUNDO)
    estilo.configure("Painel.TFrame", background=COR_PAINEL)
    estilo.configure("TLabel", background=COR_FUNDO)
    estilo.configure("Painel.TLabel", background=COR_PAINEL)
    estilo.configure("Titulo.TLabel", font=(FONTE, 16, "bold"), background=COR_PAINEL)
    estilo.configure("Sub.TLabel", font=(FONTE, 10), foreground=COR_SUAVE, background=COR_PAINEL)
    estilo.configure("Total.TLabel", font=(FONTE, 26, "bold"), foreground=COR_SUCESSO, background=COR_PAINEL)
    estilo.configure("CardValor.TLabel", font=(FONTE, 22, "bold"), background=COR_PAINEL)
    estilo.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
    estilo.configure("TNotebook.Tab", font=(FONTE, 12, "bold"), padding=(18, 8))
    estilo.configure("Treeview", font=(FONTE, 11), rowheight=30)
    estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"))
    estilo.configure("TButton", font=(FONTE, 11), padding=(10, 6))
    estilo.configure("TEntry", padding=6)


def botao(pai, texto, comando, cor=COR_PRIMARIA, grande=False, **kw):
    """Botão colorido (tk.Button aceita cor de fundo no Windows)."""
    tamanho = 13 if grande else 11
    return tk.Button(
        pai, text=texto, command=comando, bg=cor, fg="white",
        activebackground=cor, activeforeground="white",
        font=(FONTE, tamanho, "bold"), relief="flat", cursor="hand2",
        padx=14, pady=10 if grande else 6, bd=0, **kw,
    )


def tabela(pai, colunas, altura=10):
    """Treeview com barra de rolagem. colunas = [(id, titulo, largura, alinhamento)]"""
    quadro = ttk.Frame(pai, style="Painel.TFrame")
    tv = ttk.Treeview(quadro, columns=[c[0] for c in colunas], show="headings",
                      height=altura, selectmode="browse")
    for cid, titulo, largura, alinhar in colunas:
        tv.heading(cid, text=titulo, anchor=alinhar)
        tv.column(cid, width=largura, anchor=alinhar, stretch=(alinhar == "w"))
    barra = ttk.Scrollbar(quadro, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=barra.set)
    tv.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return quadro, tv


class AreaRolavel(ttk.Frame):
    """Frame com rolagem vertical (para a grade de comandas)."""

    def __init__(self, pai, bg=COR_FUNDO):
        super().__init__(pai)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interno = tk.Frame(self.canvas, bg=bg)
        self.interno.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._janela = self.canvas.create_window((0, 0), window=self.interno, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._janela, width=e.width))
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._rolar))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _rolar(self, evento):
        self.canvas.yview_scroll(int(-evento.delta / 120), "units")
