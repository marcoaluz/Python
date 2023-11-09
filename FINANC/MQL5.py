import MetaTrader5 as mt5
import pandas as pd
import time
import pytz


from datetime import datetime

# exibimos dados sobre o pacote MetaTrader5
print("MetaTrader5 package author: ",mt5.__author__)
print("MetaTrader5 package version: ",mt5.__version__)
 
# estabelecemos a conexão ao MetaTrader 5
if not mt5.initialize(login=212561885, server="OctaFX-Demo",password="2ggkfjox"):
    print("initialize() failed, error code =",mt5.last_error())
    quit()
 
# imprimimos informações sobre o estado da conexão, o nome do servidor e a conta de negociação tal qual como estão
print(mt5.terminal_info())
# imprimimos informações sobre a versão do MetaTrader 5
print(mt5.version())

terminal_info_dict=mt5.terminal_info()._asdict()
# convertemos o dicionário num DataFrame e imprimimos
df=pd.DataFrame(list(terminal_info_dict.items()),columns=['property','value'])
print("terminal_info() as dataframe:")
print(df[:-1])

# subscreva para receber atualizações no livro de ofertas para o símbolo EURUSD (Depth of Market)
if mt5.market_book_add('USDCHF'):
  # obtemos 10 vezes em um loop os dados do livro de ofertas
   for i in range(10):
        # obtemos o conteúdo do livro de ofertas (Depth of Market)
        items = mt5.market_book_get('USDCHF')
        # exibimos todo o livro de ofertas como uma string tal qual como está
        print(items)
        # agora exibimos cada solicitação separadamente para maior clareza
        if items:
            for it in items:
                # conteúdo da solicitação
                print(it._asdict())
        # vamos fazer uma pausa de 5 segundos antes da próxima solicitação de dados do livro de ofertas
        time.sleep(5)
  # cancelamos a subscrição de atualizações no livro de ofertas (Depth of Market)
   mt5.market_book_release('USDCHF')
else:
    print("mt5.market_book_add('USDCHF') failed, error code =",mt5.last_error())

# tentamos ativar a exibição do símbolo EURJPY no MarketWatch
selected=mt5.symbol_select("EURJPY",True)
if not selected:
    print("Failed to select EURJPY")
    mt5.shutdown()
    quit()
 
# imprimimos as propriedades do símbolo EURJPY
symbol_info=mt5.symbol_info("EURJPY")
if symbol_info!=None:
    # exibimos os dados sobre o terminal tal qual como estão    
    print(symbol_info)
    print("EURJPY: spread =",symbol_info.spread,"  digits =",symbol_info.digits)
    # exibimos as propriedades do símbolo como uma lista
    print("Show symbol_info(\"EURJPY\")._asdict():")
    symbol_info_dict = mt5.symbol_info("EURJPY")._asdict()
    for prop in symbol_info_dict:
        print("  {}={}".format(prop, symbol_info_dict[prop]))


pd.set_option('display.max_columns', 500) # número de colunas
pd.set_option('display.width', 1500)      # largura máxima da tabela


# definimos o fuso horário como UTC
timezone = pytz.timezone("Etc/UTC")
# criamos o objeto datetime no fuso horário UTC para que não seja aplicado o deslocamento do fuso horário local
utc_from = datetime(2020, 1, 10, tzinfo=timezone)
# recebemos 10 barras de EURUSD H4 a partir de 01/10/2019 no fuso horário UTC
rates = mt5.copy_rates_from("EURUSD", mt5.TIMEFRAME_H4, utc_from, 10)
 

# concluímos a conexão ao terminal MetaTrader 5
mt5.shutdown()

print("Exibimos os dados recebidos como estão")
for rate in rates:
    print(rate)
 
# a partir dos dados recebidos criamos o DataFrame
rates_frame = pd.DataFrame(rates)
# convertemos o tempo em segundos no formato datetime
rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
                           
# exibimos dados
print("\nExibimos o dataframe com dados")
print(rates_frame)  
 