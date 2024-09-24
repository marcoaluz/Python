import MetaTrader5 as mt5

mt5.initialize()

d = mt5.terminal_info()

d = d._asdict()


for k in d.keys():
    print(k," ->", d[k])

dados = mt5.COPY_TICKS_FROM(symbol, date_from, count, flags)
