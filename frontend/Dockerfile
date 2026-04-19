# ── Stage 1: Build ──────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# COPY package.json package-lock.json* ./
# RUN npm ci --silent

COPY package.json ./
RUN npm install --silent

COPY . .
RUN npm run build

# ── Stage 2: Serve via nginx ─────────────────────────────────
FROM nginx:1.25-alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
