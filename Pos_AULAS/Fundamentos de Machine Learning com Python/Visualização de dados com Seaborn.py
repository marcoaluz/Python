import pandas as pd


dados_df = pd.read_csv('C:/Python/Pos_AULAS/Fundamentos de Machine Learning com Python/bank-full-aula.csv', delimiter = ';')

print(dados_df)


print(list(dados_df.columns))
print(dados_df.dtypes)

#Primeiro elemento da base : .head()

print(dados_df.head(3))


#elementos finais da base: .TAIL()
print(dados_df.tail())

#Amostra aleatória da base: sample()

print(dados_df.sample(50))

#Analise exploratoria inicial dos dados

print(dados_df.describe())

# Explorando os campos com dados categoricos(object)



print(dados_df['education'].unique())

#Aoenas os valores nulos de education

unknown_count = dados_df[dados_df['education'] == 'unknown']

print(unknown_count)