FROM node:18-alpine

WORKDIR /app

# 拷贝包配置并安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 拷贝源代码
COPY index.js ./
RUN chmod +x index.js

# 默认环境变量
ENV ARL_HOST=""
ENV ARL_TOKEN=""
ENV SSE=""
ENV PORT="3100"

# 默认使用 stdio 模式；传 --sse 或 SSE=true 开启 HTTP SSE 模式
ENTRYPOINT ["node", "index.js"]
