# ---------- Build stage ----------
    FROM node:18-alpine AS build

    WORKDIR /app
    
    COPY package.json package-lock.json* ./
    RUN npm install
    
    COPY . .
    
    ARG REACT_APP_API_URL=http://localhost:5000/api
    ENV REACT_APP_API_URL=$REACT_APP_API_URL
    
    RUN npm run build
    
    # ---------- Production stage ----------
    FROM nginx:alpine
    
    # Remove default nginx config
    RUN rm /etc/nginx/conf.d/default.conf
    
    # Copy built React app
    COPY --from=build /app/build /usr/share/nginx/html
    
    # Copy NGINX server config
    COPY nginx/default.conf /etc/nginx/conf.d/default.conf
    
    EXPOSE 80
    
    HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
      CMD wget --quiet --tries=1 --spider http://localhost || exit 1
    
    CMD ["nginx", "-g", "daemon off;"]
    