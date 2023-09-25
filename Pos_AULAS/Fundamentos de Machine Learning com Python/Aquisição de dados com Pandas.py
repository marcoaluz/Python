import pandas as pd


alunos_df = pd.DataFrame([['Ana',22],['Bia',21],['Carlos',24]], columns=['nome','idade'])

print(alunos_df)

nomes_alunos = ['Ana','Bia','Carlos','Douglas','Erik']
idade_alunos = [22,21,24,21,23]
notas_prova_1 =[9.5, 8.0, 7.7, 8.5, 9.0]

alunos_df = pd.DataFrame({'nome':nomes_alunos, 'idade':idade_alunos, 'prova_1': notas_prova_1})

print(alunos_df)

#Idexação em um DataFrame

print(alunos_df[['nome', 'idade']])



# Series são colunas do DataFrame

idade_series = pd.Series(idade_alunos, name = 'idade')

print(idade_series)

#Lista de nomes das colunas

print(alunos_df.columns)
print(alunos_df.columns.values)
print(type(alunos_df.columns.values))

#Valores das colunas

print(alunos_df['idade'].values)
print(type(alunos_df['idade'].values))

#media de idade
print(alunos_df['idade'].values.mean())


#Mais uma forma de construir um DataFrame

del alunos_df

alunos_df = pd.DataFrame()

print(alunos_df)

#Atribuir as colunas via idexação

nome_serie = pd.Series(nomes_alunos)

alunos_df['nome'] = nome_serie

print(alunos_df)

idade_series = pd.Series(idade_alunos)

alunos_df['idade'] = idade_series

alunos_df['prova_1'] = notas_prova_1

print(alunos_df)


#Analise Exploratória dos dados numericos

print(alunos_df.describe())

#filtros de dados

print(alunos_df['idade']>=22)

print(alunos_df[alunos_df['idade']>=22])
print(alunos_df[alunos_df['prova_1']> 8.])
print(alunos_df[ (alunos_df['idade']>=22) & (alunos_df['prova_1'] >8)])


#Operador Loc

print(alunos_df.loc[alunos_df['idade'] >=22])



#isin = comparar obejto

lista_nomes_grupo_1 = ['Ana','Carlos','Gustavo']

print(alunos_df[alunos_df['nome'].isin(lista_nomes_grupo_1)])

print(alunos_df[alunos_df['nome'].isin(lista_nomes_grupo_1) & (alunos_df['prova_1']>8)])

print(alunos_df[alunos_df['nome'].isin(lista_nomes_grupo_1) | (alunos_df['prova_1']> 8)])

print(type(alunos_df[alunos_df['nome'].isin(lista_nomes_grupo_1)]))

#Realizar compraração e selecionar apenas as colunas necessaria
print(alunos_df[alunos_df['nome'].isin(lista_nomes_grupo_1) | (alunos_df['prova_1']> 8)][['nome','prova_1']])


#Salvar um dataFrame em arquivo

print(alunos_df.to_csv('Alunos.csv', index= False, header=True))



#Importar um arquivo CSV
data_df = pd.read_csv('C:/Python/Pos_AULAS/Fundamentos de Machine Learning com Python/bank-full-aula.csv', delimiter=';')


print(data_df)