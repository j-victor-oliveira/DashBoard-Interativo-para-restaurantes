# Fase 1: Construir a aplicação React
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV CI=true

# Constrói a aplicação para produção
RUN npm run build

# Fase 2: Servir a aplicação construída com Nginx
FROM nginx:1.25-alpine

# Copia os ficheiros estáticos construídos (HTML, CSS, JS) da fase de 'build'
# para a pasta que o Nginx usa para servir sites
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 3000

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]