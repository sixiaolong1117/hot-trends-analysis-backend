# ==== 构建前端 ====
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend_src /frontend
RUN npm install && npm run build

# ==== 构建后端 ====
FROM python:3.11-slim
WORKDIR /app

# 复制 Python 后端
COPY app /app

# 复制前端构建结果
COPY --from=frontend /frontend/dist /app/frontend

RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
