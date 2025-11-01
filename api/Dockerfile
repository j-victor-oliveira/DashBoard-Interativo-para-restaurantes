# Comece com uma imagem Python
FROM python:3.11-slim

# Defina o diretório de trabalho
WORKDIR /app

# Instala o 'curl' (para o healthcheck) E o pacote de 'locales'
RUN apt-get update && apt-get install -y curl locales && \
    # Gera o locale pt_BR.UTF-8
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    # Limpa o cache
    rm -rf /var/lib/apt/lists/*

# Define o locale gerado como o padrão para todo o container
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR:pt
ENV LC_ALL pt_BR.UTF-8

# Copie o ficheiro de dependências
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o resto do código da API
COPY . .

# Comando para executar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

