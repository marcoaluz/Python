frutas = ["laranja", "maca", "uva"]
frutas[-1]
print(frutas)

Valor = [10,5,6]
print("Valor da ",frutas[-1],Valor[0])

frutas = []
print(frutas)

letras = list("python")
print(letras)

numeros = list(range(10))
print(numeros)

carro = ["Ferrari", "F8", 4200000, 2020, 2900, "São Paulo", True]
print(carro)


# lista alinhada é conhecido como matriz bidimensional


matriz = [
[1,"a",2],
["b",3,4],
[6,5,"c"]
]


matriz[0]
matriz[0][0]
matriz[0][-1]
matriz[-1][-1]

# Fatiamento 
# Alem de acessar elementos diretamente, podemos extrair um conjunto de valores de uma sequencia. para isso basta passar o indece inicial e/ou final para acessar o
# conjunto, podemos ainda informar quantas possições o cursor deve "pulr" no caso

lista = ["p", "y", "t", "h", "o", "n"]

lista[2:] #["t", "h", "o", "n"]
lista[:2]  #["p", "y"]
lista[1:3] #[ "y", "t"]
lista[0:3:2] #["p", "t",]
lista[::]    #["p", "y", "t", "h", "o", "n"]
lista[::-1]  #["n","o","h","t","y","p" ] 



# carros = ["gol","celta","palio"]

# for carro in carros:
#     Print(carro)


# lista utilizando comprehension

numeros = [1,30,21,2,9,65,34]
quadrado = [numero ** 2 for numero in numeros]
pares =[numero for numero in numeros if numero % 2 == 0]

print(pares)
print (quadrado)

# Merodos das Classe Lis

# Append serve para adicionar um valor na lista
Lista = []

lista.append(1)
lista.append("Python")
lista.append([40,30,20])

print(lista)

lista = [1, "Python",[40,30,20]]

lista.clear() #limpar a lista 
lista.copy()

print(lista)


#[].count  conta a quantidade de vezes objeto é apresentado na lista

cores = ["vermelho","azul","verde","azul"]

cores.count("vermelho") # 1
cores.count("azul") # 2
cores.count("verde") #1

# [].extend adicionar a lista valores que for passado no extend adiciona varios elementos

linguagens = ["python","js","c"]

print(linguagens) # ["python","js","c"]

linguagens.extend(["java","csharp"])

print(linguagens) # ["python","js","c","java","csharp"]


# [].index ele que saber onde esta objeto passado na lista ele localiza primeira aparição

linguagens = ["python","java","c","java","csharp"]

print(linguagens.index("java")) # 3
print(linguagens.index("python")) # 0

# [].pop retirar o ultimo elemento da lista (pilha) mas pode ser passado qual elemento ele quer retirar 0,1,2

linguagens = ["python","js","c","java","csharp"]

linguagens.pop() #csharp
linguagens.pop() #java
linguagens.pop() #c
linguagens.pop(0) #python

# [].remove é sugunda forma de retirar um valor da sua lista mas diferente do pop q passa o index ele passa o objeto desejado
# ele retira sempre o primeiro elemento que é encontrado

linguagens = ["python","js","c","java","csharp"]

linguagens.remove("C")

print(linguagens) #["python","js","java","csharp"]

# [].reverse ele reverte os valores da sua lista

linguagens = ["python","js","c","java","csharp"]

linguagens.reverse()

print(linguagens) # ["csharp","java","c","js","python"]

# [].sort serve para ordenar valores dentro da sua lista segue alguns exemplos 

linguagens = ["python","js","c","java","csharp"]
linguagens.sort() # ["c","csharp","java","js","python"]

# ordenar por ordem alfabetica mas revertindo a lista
linguagens = ["python","js","c","java","csharp"]
linguagens.sort(reverse=True) #["python","js","java","csharp","c"]

# ordena por tamanho do objeto dentro da lista do menor para maior ele conta os elementos
linguagens = ["python","js","c","java","csharp"]
linguagens.sort(key=lambda x: len(x)) #["c","js","java","python","csharp"]

#ordena por tamanho mas do maior para menor e caso objeto tenha o mesmo tamanho ele vai pegar o primeiro 
linguagens = ["python","js","c","java","csharp"]
linguagens.sort(key=lambda x: len(x), reverse=True) # ["python","csharp","java","js","c"]


#len verifica o tamanho do objeto ou da lista
linguagens = ["python","js","c","java","csharp"]

len(linguagens) #5 

# sorted serve para ordenar interaveis 

linguagens = ["python","js","c","java","csharp"]

sorted(linguagens, key=lambda x: len(x)) #["c","js","java","python","csharp"]
sorted(linguagens, key=lambda x: len(x),reverse=True)  # ["python","csharp","java","js","c"]

