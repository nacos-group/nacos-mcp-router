FROM python:3.12-slim
# 安装系统依赖
RUN apt-get update && apt-get install -y build-essential curl && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install uv
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
RUN apt-get install -y nodejs

WORKDIR /app

COPY src/python .

RUN mkdir -p /root/.cache/chroma/onnx_models/all-MiniLM-L6-v2/
RUN curl -v https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz -o /root/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx.tar.gz

# 安装 Python 依赖
# RUN pip install nacos-mcp-router==${ROUTER_VERSION}
RUN pip install --no-cache-dir .

# 启动服务
CMD ["python", "-m", "nacos_mcp_router"]