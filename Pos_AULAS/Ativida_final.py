import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Suponha que você já carregou os dados de treinamento e teste (X_train, X_test, y_train, y_test)

# Pré-processamento de textos (remoção de pontuação e tokenização)
X_train_processed = [text.lower().split() for text in X_train]
X_test_processed = [text.lower().split() for text in X_test]

# Representação de textos com Bag of Words (BoW)
vectorizer = CountVectorizer()
X_train_bow = vectorizer.fit_transform(X_train_processed)
X_test_bow = vectorizer.transform(X_test_processed)

# Treinamento do classificador (Regressão Logística) com BoW
classifier_bow = LogisticRegression()
classifier_bow.fit(X_train_bow, y_train)

# Previsões com BoW
y_pred_bow = classifier_bow.predict(X_test_bow)

# Avaliação de desempenho com BoW
accuracy_bow = accuracy_score(y_test, y_pred_bow)
precision_bow = precision_score(y_test, y_pred_bow)
recall_bow = recall_score(y_test, y_pred_bow)
f1_score_bow = f1_score(y_test, y_pred_bow)

print("Acurácia (BoW):", accuracy_bow)
print("Precisão (BoW):", precision_bow)
print("Revocação (BoW):", recall_bow)
print("F1-Score (BoW):", f1_score_bow)