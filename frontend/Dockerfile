# ══════════════════════════════════════════════════════════════
# Sales Insight Automator — Frontend Dockerfile
# Multi-stage: Node 20 build → nginx:alpine serve
# ══════════════════════════════════════════════════════════════

# ── Build Stage ───────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies first for caching
COPY package.json package-lock.json* ./
RUN npm ci --silent 2>/dev/null || npm install --silent

# Copy source and build
COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ── Production Stage ──────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Custom nginx config
COPY --from=build /app/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
