# Importe as bibliotecas necessárias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report

# 1. Aquisição e leitura dos dados
data = pd.read_csv('vinhos.csv')

# 2. Análise exploratória
# Examine as principais características da base de dados, como estatísticas descritivas e gráficos.

# 3. Preparação dos dados
# Escolha uma das atividades de classificação (a ou b) e prepare os dados de acordo.

# a. Classificação de vinho do tipo 'tinto' ou 'branco'
# Selecione as features relevantes e os rótulos (tinto ou branco).

# Ou

# b. Classificação entre os vinhos com qualidade superior ou inferior a 6
# Defina os critérios para "qualidade superior" e "inferior" e crie os rótulos correspondentes.

# 4. Separação dos conjuntos de treino e teste
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# 5. Modelagem
# Treine modelos de classificação, como o SVM.
model = SVC()
model.fit(X_train, y_train)

# 6. Avaliação dos resultados
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

# Exiba a acurácia e relatório de classificação
print("Acurácia:", accuracy)
print("Relatório de Classificação:")
print(report)
