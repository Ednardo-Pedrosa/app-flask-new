# Usar uma imagem base oficial do Python
FROM python:3.9-slim

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copiar o arquivo requirements.txt para o contêiner
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação para o diretório de trabalho no contêiner
COPY . .

# Expor a porta que a aplicação Flask usará
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]
