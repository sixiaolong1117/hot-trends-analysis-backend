from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import subprocess, json, os
import asyncio

app = FastAPI(title="Hot Trends Analyzer")

frontend_dir = "/app/frontend"
assets_dir = os.path.join(frontend_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    print(f"⚠️ Warning: assets directory not found at {assets_dir}")

@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")

# 从环境变量读取 API 地址
OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
HOT_SEARCH_API = os.getenv("HOT_SEARCH_API", "http://localhost:8000/hot-search")
DEFAULT_PLATFORMS = os.environ.get("DEFAULT_PLATFORMS", "weibo,zhihu,baidu,douyin")

@app.get("/api/config")
async def get_config():
    return {
        "ollama_api": OLLAMA_API,
        "hot_search_api": HOT_SEARCH_API,
        "default_platforms": DEFAULT_PLATFORMS
    }

class AnalysisRequest(BaseModel):
    ollama_model: str = "qwen2.5:14b"
    topics_per_platform: int = 10
    platforms: list[str] = [
        "weibo", "zhihu", "baidu", "douyin"
    ]


async def stream_logs(cmd: list, save_dir: str):
    """流式输出日志的生成器"""
    log_file_path = os.path.join(save_dir, "run.log")
    
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            # 添加环境变量强制 Python 不缓冲输出
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # 实时读取并发送日志
            for line in iter(process.stdout.readline, ''):
                if line:
                    line = line.rstrip()
                    print(line, flush=True)  # 输出到 Docker 日志
                    log_file.write(line + "\n")
                    log_file.flush()
                    
                    # 发送 SSE 格式的日志
                    yield f"data: {json.dumps({'type': 'log', 'message': line})}\n\n"
                    await asyncio.sleep(0)  # 让出控制权
            
            process.stdout.close()
            returncode = process.wait()
            
            if returncode != 0:
                error_msg = f"Analyzer 执行失败，退出码: {returncode}，日志见 {log_file_path}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            # 查找生成的结果文件
            files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
            if not files:
                error_msg = f"未生成分析结果，日志见 {log_file_path}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            result_file = os.path.join(save_dir, files[0])
            with open(result_file, "r", encoding="utf-8") as f:
                result_data = json.load(f)
            
            # 发送完成信号和结果
            yield f"data: {json.dumps({'type': 'complete', 'result': result_data})}\n\n"
            
    except Exception as e:
        error_msg = f"执行出错: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"


@app.post("/api/analyze-stream")
async def analyze_stream(req: AnalysisRequest):
    """流式分析接口，使用 SSE 实时返回日志"""
    save_dir = "/app/outputs"
    os.makedirs(save_dir, exist_ok=True)

    cmd = [
        "python", "/app/analyzer.py",
        "--hot-search-api", HOT_SEARCH_API,
        "--ollama-api", OLLAMA_API,
        "--ollama-model", req.ollama_model,
        "--save-dir", save_dir,
        "--topics-per-platform", str(req.topics_per_platform)
    ]
    cmd += ["--platforms"] + req.platforms

    return StreamingResponse(
        stream_logs(cmd, save_dir),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    """保留原有的非流式接口作为备用"""
    save_dir = "/app/outputs"
    os.makedirs(save_dir, exist_ok=True)

    cmd = [
        "python", "/app/analyzer.py",
        "--hot-search-api", HOT_SEARCH_API,
        "--ollama-api", OLLAMA_API,
        "--ollama-model", req.ollama_model,
        "--save-dir", save_dir,
        "--topics-per-platform", str(req.topics_per_platform)
    ]
    cmd += ["--platforms"] + req.platforms

    try:
        log_file_path = os.path.join(save_dir, "run.log")
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.strip(), flush=True)
                    log_file.write(line)
            process.stdout.close()
            returncode = process.wait()

        if returncode != 0:
            raise HTTPException(status_code=500, detail=f"Analyzer 执行失败，日志见 {log_file_path}")

        files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
        if not files:
            raise HTTPException(status_code=500, detail=f"未生成分析结果，日志见 {log_file_path}")
        result_file = os.path.join(save_dir, files[0])
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Analyzer 执行失败，日志见 {log_file_path}")