import MetaTrader5 as mt5
import requests

#api_url = 'https://trade.metatrader5.com/terminal'#

print("MetaTrader5 package author: ",mt5.__author__)
print("MetaTrader5 package version: ",mt5.__version__)


mt5.initialize(
   path = 'https://trade.metatrader5.com/terminal',                  #   // caminho para o arquivo EXE do terminal MetaTrader 5
   login=5018727141,              #// número da conta
   password="O@FbHp4g",      #// senha
   server="MetaQuotes-Demo",          #// nome do servidor conforme definido no terminal
   timeout=5,          #// tempo de espera esgotado
   portable=False            #// modo portable
   )
print("initialize() failed, error code =",mt5.last_error())
# estabelecemos a conexão com o terminal MetaTrader 5 para a conta especificada

print(mt5.terminal_info())
# imprimimos informações sobre a versão do MetaTrader 5
print(mt5.version())

#
#


