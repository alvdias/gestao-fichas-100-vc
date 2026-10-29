GESTÃO DE COMANDAS PARA BARES  —  v1.0
========================================

COMO GERAR O EXECUTÁVEL (só uma vez, em qualquer Windows 11)
------------------------------------------------------------
1. Instale o Python 3.12 (64 bits): https://www.python.org/downloads/windows/
   -> Na instalação, MARQUE a opção "Add python.exe to PATH".
2. Descompacte este .zip numa pasta (ex.: C:\GestaoComandas).
3. Dê dois cliques em  GERAR_EXECUTAVEL.bat  e espere 1-2 minutos.
4. Vai aparecer o arquivo  GestaoComandas.exe  na pasta.

Pronto: esse .exe roda sozinho em qualquer Windows 11, sem precisar
instalar Python no computador do bar. Basta copiar o .exe.

Primeira vez que abrir: o Windows pode mostrar "O Windows protegeu o
computador" (SmartScreen), porque o programa não tem assinatura digital.
Clique em "Mais informações" -> "Executar assim mesmo". Só acontece uma vez.


COMO USAR NO DIA A DIA
----------------------
ABRIR COMANDA ....... "+ Nova comanda" (ou F2). O número já vem sugerido;
                      nome do cliente é opcional.
LANÇAR PRODUTO ...... Clique na comanda, digite parte do nome do produto
                      (ex.: "cai" para Caipirinha) e tecle Enter.
                      Ou duplo clique no produto. Use − / + para a quantidade.
                      Botões de categoria filtram a lista (Cervejas, Drinks...).
CANCELAR ITEM ....... Selecione o item e clique em "Cancelar item" (ou Del).
                      O item fica riscado e sai do total.
DIVIDIR A CONTA ..... Campo "Dividir por" mostra o valor por pessoa.
FECHAR COMANDA ...... "Fechar comanda" (ou F9). Mostra o total e, se quiser,
                      calcula o troco. O estoque é baixado nesse momento.
PRODUTOS ............ Aba "Produtos e estoque": cadastrar, editar preço,
                      desativar e dar entrada de mercadoria.
                      Em vermelho = 5 unidades ou menos disponíveis.
RELATÓRIO ........... Aba "Relatório do dia": total vendido, comandas
                      fechadas, ticket médio e produtos mais vendidos.
                      Use ◀ ▶ para ver outros dias.

Estoque "Disponível" = estoque menos o que já está lançado em comandas
abertas. Se tentar lançar além disso, o sistema avisa antes.


ONDE FICAM OS DADOS / BACKUP
----------------------------
Tudo fica no arquivo  fichas.db , na mesma pasta do GestaoComandas.exe.
(Se a pasta não permitir gravação, ex. C:\Program Files, os dados vão
para %LOCALAPPDATA%\GestaoFichas.) O caminho aparece no rodapé do sistema.

BACKUP = copiar o arquivo fichas.db para um pendrive ou nuvem.
Para trocar de computador: copie o .exe e o fichas.db juntos.
Comandas abertas continuam salvas mesmo se fechar o programa ou faltar luz.


PARA DESENVOLVEDORES
--------------------
Rodar sem gerar .exe:  python main.py
Testes das regras:     python testes.py
Estrutura: main.py (janela) · database.py (SQLite) · services.py (regras)
           telas/ (comandas, produtos, relatorio, estilo)
