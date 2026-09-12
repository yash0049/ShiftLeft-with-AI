# ---- dependencies -----------------------------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- production bundle ------------------------------------------------------
FROM deps AS build
WORKDIR /app
COPY . .
RUN npm run build

# ---- test runner ------------------------------------------------------------
# Built only when requested with --target test; `docker build` without a target
# stops at the runtime stage below, which does not depend on this one.
FROM deps AS test
WORKDIR /app
COPY . .
CMD ["npm", "run", "test"]

# ---- runtime ----------------------------------------------------------------
# Last stage, so a plain `docker build` produces the nginx image.
FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
