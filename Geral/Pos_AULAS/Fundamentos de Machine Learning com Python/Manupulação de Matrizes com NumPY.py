#NumPY processar matriz 

import numpy as np  # Importe o NumPy e dê um apelido (np) para ele


lista = [[1, 1, 0], 
         [0, 0, 1]]  # Use colchetes para definir listas aninhadas


array = np.array(lista)

print(array[1,0])

print(array.ndim) # Numero de dimensão do meu array
print(array.shape) # formato/Estrutura da matriz do array no exemplo 2 linha e 3 coluna 
print(array.size) # Quantidade de informação no array
print(array.dtype) # Tipo de formatação do dados
print(array.itemsize) # Tamanho do Item
print(array.data) #Buffer dos elementos do array

array = np.zeros(5) #tamanho do array é 5 e zerados

print(array)

array = np.zeros([5,3])

print(array)

array = np.ones(5) #tamanho do array é 5 e 1

print(array)

# Criação de um array não inicializado 0 conteudo pode varias, lixo de memoria, comum em C,
array = np.empty(10) 

print(array)

#Criação similiar a função ranger[] criando valores de  ate o indice indicado -1

array = np.arange(0,10)

print(array)

#criação de um array com valores aleatorio de 0 a 1 no elementos.

array = np.random.random([2,3])

print(array)

#ajustes na dimensão do array

array = np.zeros(10).reshape([5,2])

print(array)

# Array com soma, maximo e minimo

array = lista

array = np.sum(lista)

print(array)

array = np.max(lista)

print(array)

array = np.min(lista)

print(array)

#Array com Operações Matriciais Basicas

a = np.arange(6).reshape(2,3)

print(a)

#soma
a  = a + 1
print(a)
#subtração
a  = a - 1
print(a)
#multiplicação
a  = a * 1
print(a)
#Divisão
a  = a / 1
print(a)
#Exponenciação
a  = a ** 2
print(a)

#Exponenciação de um fração 
a  = a ** (1/2)
print(a)


#entender sobre o @

#Matriz Transposta 


# Indexação

array = np.arange(10*8).reshape([10,8])

print(array)

#partiçõe e corte do array do inicio ate 5 linha
arrays = array[:5]
print(arrays)

#partiçõe e corte do array do inicia na 5 linha e vai ate final

arrays = array[5:]
print(arrays)

#partiçõe e corte do array apenas a primeira coluna

arrays = array[:,0]
print(arrays)

#partiçõe e corte do array apenas todas colunas conforme necessidade no array

arrays = array[3:7,:3]
print(arrays)

arrays = array[3:7,3:]
print(arrays)

arrays = array[3:7,3:6]
print(arrays)

#Elemento de uma Matriz

arrays = array[1]
print(arrays)

#Manipulação Matricial

MAN = np.random.random([10*10])

print(MAN.shape)
print(MAN.max())
print(MAN.min())

MAN = MAN*100

print(MAN)

MAN = MAN.astype(np.int16)

print(MAN)
print(MAN.std())
print(MAN.shape)
print(MAN.max())
print(MAN.min())

MAN = MAN >48
print(MAN)

#Pegar o valor do array e não condição verdadeiro ou falso
array = MAN[MAN > 48]
print(array)

array = MAN[MAN<48] = 0
print(MAN)