import MetaTrader5 as mt5
import pandas as pd

# display data on the MetaTrader 5 package
print("MetaTrader5 package author: ",mt5.__author__)
print("MetaTrader5 package version: ",mt5.__version__)
 
# establish MetaTrader 5 connection to a specified trading account
if not mt5.initialize(login=212561885, server="OctaFX-Demo",password="2ggkfjox"):
    print("initialize() failed, error code =",mt5.last_error())
    quit()
 
# display data on connection status, server name and trading account
print(mt5.terminal_info())
# display data on MetaTrader 5 version
print(mt5.version())

terminal_info_dict=mt5.terminal_info()._asdict()
# convertemos o dicionário num DataFrame e imprimimos
df=pd.DataFrame(list(terminal_info_dict.items()),columns=['property','value'])
print("terminal_info() as dataframe:")
print(df[:-1])

# shut down connection to the MetaTrader 5 terminal
mt5.shutdown()

