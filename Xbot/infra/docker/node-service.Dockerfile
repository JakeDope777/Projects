FROM node:20-alpine AS base
WORKDIR /app

COPY package.json tsconfig.base.json ./
COPY packages ./packages
COPY apps ./apps

RUN npm install

ARG SERVICE_PATH
ENV SERVICE_PATH=${SERVICE_PATH}

CMD ["sh", "-c", "npm run dev --workspace ${SERVICE_PATH}"]

