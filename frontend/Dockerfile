
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Build 결과물만 복사하는 stage
FROM alpine:latest AS export-stage
WORKDIR /export
COPY --from=builder /app/dist ./dist
