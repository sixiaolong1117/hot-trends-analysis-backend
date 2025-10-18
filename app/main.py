from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess, json, os

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
DEFAULT_PLATFORMS = os.environ.get("DEFAULT_PLATFORMS", "weibo,zhihu,baidu,douyin,toutiao")
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
        "weibo", "zhihu", "baidu", "bilibili", "douyin",
        "toutiao", "36kr", "ithome", "github", "hackernews"
    ]


@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
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
        # 捕获输出到日志文件
        log_file_path = os.path.join(save_dir, "run.log")
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            # 实时写文件并打印
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.strip(), flush=True)   # 输出到 Docker 日志
                    log_file.write(line)               # 写入日志文件
            process.stdout.close()
            returncode = process.wait()

        if returncode != 0:
            raise HTTPException(status_code=500, detail=f"Analyzer 执行失败，日志见 {log_file_path}")


        # 返回生成的 JSON 文件
        files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
        if not files:
            raise HTTPException(status_code=500, detail=f"未生成分析结果，日志见 {log_file_path}")
        result_file = os.path.join(save_dir, files[0])
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Analyzer 执行失败，日志见 {log_file_path}")

