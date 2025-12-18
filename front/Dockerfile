### Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY front/package.json front/package-lock.json* ./
COPY front/ ./
RUN npm ci --silent
RUN npm run build

### Production stage
FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Optional: copy custom nginx config if needed
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
