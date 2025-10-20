import requests
import json
from typing import List, Dict
import time
import os
import argparse
import sys

sys.stdout.reconfigure(line_buffering=True)

def parse_args():
    parser = argparse.ArgumentParser(
        description="网络热搜分析工具 - 可配置化版本 (Powered by Ollama)"
    )

    parser.add_argument("--hot-search-api", type=str, required=True,
                        help="热搜数据接口地址，例如 http://192.168.0.1:10880")

    parser.add_argument("--ollama-api", type=str, required=True,
                        help="Ollama API 地址，例如 http://192.168.0.1:11434")

    parser.add_argument("--ollama-model", type=str, default="qwen2.5:14b",
                        help="Ollama 模型名称（默认：qwen2.5:14b）")

    parser.add_argument("--save-dir", type=str, default=os.path.expanduser("~/hot_trends_analysis/outputs"),
                        help="结果保存目录")

    parser.add_argument("--platforms", type=str, nargs="+", default=[
        "weibo", "zhihu", "baidu", "bilibili", "douyin",
        "toutiao", "36kr", "ithome", "github", "hackernews"
    ], help="要分析的平台列表（空格分隔）")

    parser.add_argument("--topics-per-platform", type=int, default=10,
                        help="每个平台提取的热搜条数")

    parser.add_argument("--max-retries", type=int, default=5,
                        help="最大重试次数")

    parser.add_argument("--retry-delay", type=float, default=5,
                        help="重试等待时间（秒）")

    return parser.parse_args()


def fetch_hot_search(platform: str, api_url: str, max_retries: int, retry_delay: float) -> Dict:
    """获取指定平台的热搜数据，失败后自动重试"""
    for attempt in range(1, max_retries + 1):
        try:
            url = f"{api_url}/{platform}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️  获取 {platform} 数据失败 (尝试 {attempt}/{max_retries}): {e}", flush=True)
                print(f"   等待 {retry_delay} 秒后重试...", flush=True)
                time.sleep(retry_delay)
            else:
                print(f"❌ 获取 {platform} 数据失败，已重试 {max_retries} 次: {e}", flush=True)
                return None
    return None


def extract_hot_topics(data: Dict, platform: str, topics_per_platform: int) -> List[str]:
    """从API返回的数据中提取热搜标题"""
    topics = []
    try:
        if data and "data" in data:
            items = data["data"]
            for item in items[:topics_per_platform]:
                title = item.get("title", "")
                if title:
                    topics.append(title)
    except Exception as e:
        print(f"⚠️  解析 {platform} 数据时出错: {e}", flush=True)
    return topics


def call_ollama(prompt: str, ollama_api: str, model_name: str,
                max_retries: int, retry_delay: float) -> str:
    """调用本地Ollama进行分析，失败后自动重试"""
    for attempt in range(1, max_retries + 1):
        try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 800,
                    "num_ctx": 2048
                }
            }

            chat_api = f"{ollama_api}/api/chat"
            if attempt == 1:
                print(f"🔗 调用 Ollama API: {chat_api}", flush=True)

            response = requests.post(chat_api, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()

            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            return ""
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️  Ollama 调用失败 (尝试 {attempt}/{max_retries}): {e}", flush=True)
                print(f"   等待 {retry_delay} 秒后重试...", flush=True)
                time.sleep(retry_delay)
            else:
                print(f"❌ Ollama 调用失败，已重试 {max_retries} 次: {e}", flush=True)
                return ""
    return ""


def ensure_ollama_model(ollama_api: str, model_name: str) -> bool:
    """检查模型是否存在，不存在则自动拉取"""
    try:
        response = requests.get(f"{ollama_api}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]

        if model_name in model_names:
            print(f"✅ 模型已存在: {model_name}", flush=True)
            return True

        print(f"📦 模型不存在，正在拉取: {model_name} ...", flush=True)
        pull_response = requests.post(f"{ollama_api}/api/pull", json={"name": model_name}, stream=True, timeout=600)

        for line in pull_response.iter_lines():
            if line:
                try:
                    msg = json.loads(line.decode('utf-8'))
                    status = msg.get("status")
                    if status:
                        print(f"   {status}", flush=True)
                except json.JSONDecodeError:
                    pass

        print(f"✅ 模型拉取完成: {model_name}", flush=True)
        return True
    except Exception as e:
        print(f"❌ 检查/拉取模型时出错: {e}", flush=True)
        return False


def analyze_hot_trends(args):
    """主函数：分析网络热门趋势"""
    print("🚀 开始收集热搜数据...\n", flush=True)

    if not ensure_ollama_model(args.ollama_api, args.ollama_model):
        print("❌ 无法准备 Ollama 模型，终止分析。", flush=True)
        return

    all_topics = {}

    for platform in args.platforms:
        print(f"📡 正在获取 {platform} 热搜...", flush=True)
        data = fetch_hot_search(platform, args.hot_search_api, args.max_retries, args.retry_delay)

        if data:
            topics = extract_hot_topics(data, platform, args.topics_per_platform)
            if topics:
                all_topics[platform] = topics
                print(f"✅ {platform}: 获取到 {len(topics)} 条热搜", flush=True)
            else:
                print(f"⚠️  {platform}: 未能提取到热搜内容", flush=True)

        time.sleep(0.5)

    if not all_topics:
        print("\n❌ 未能获取到任何热搜数据，请检查API服务是否正常", flush=True)
        return

    print("\n" + "="*60, flush=True)
    print("🤖 正在使用 Ollama 分析热搜趋势...", flush=True)
    print("="*60 + "\n", flush=True)

    topics_text = ""
    for platform, topics in all_topics.items():
        topics_text += f"\n【{platform}】\n"
        for i, topic in enumerate(topics, 1):
            topics_text += f"{i}. {topic}\n"

    prompt = f"""请阅读以下来自多个平台的热搜数据，写一篇流畅的总结报告，描述当前网络热门趋势。

要求：
- 用自然流畅的段落形式写作，不要使用分点列表或标题
- 要将趋势分析和具体事实有机结合，尤其要明确指出信源哪个平台、原始内容是什么
- 被多个平台提到的内容重点分析
- 在文末列举出被全网所关注的原始内容
- 全文控制在300-500字，语言专业但易读
- 需要注意平台调用名称和站点名的对应关系，在文中要使用站点名：
| **站点**         | **类别**     | **调用名称**   |
| ---------------- | ------------ | -------------- | 
| 哔哩哔哩         | 热门榜       | bilibili       | 
| AcFun            | 排行榜       | acfun          | 
| 微博             | 热搜榜       | weibo          | 
| 知乎             | 热榜         | zhihu          | 
| 知乎日报         | 推荐榜       | zhihu-daily    | 
| 百度             | 热搜榜       | baidu          | 
| 抖音             | 热点榜       | douyin         | 
| 快手             | 热点榜       | kuaishou       | 
| 豆瓣电影         | 新片榜       | douban-movie   | 
| 豆瓣讨论小组     | 讨论精选     | douban-group   | 
| 百度贴吧         | 热议榜       | tieba          | 
| 少数派           | 热榜         | sspai          | 
| IT之家           | 热榜         | ithome         | 
| IT之家「喜加一」 | 最新动态     | ithome-xijiayi | 
| 简书             | 热门推荐     | jianshu        | 
| 果壳             | 热门文章     | guokr          | 
| 澎湃新闻         | 热榜         | thepaper       | 
| 今日头条         | 热榜         | toutiao        | 
| 36 氪            | 热榜         | 36kr           | 
| 51CTO            | 推荐榜       | 51cto          | 
| CSDN             | 排行榜       | csdn           | 
| NodeSeek         | 最新动态     | nodeseek       | 
| 稀土掘金         | 热榜         | juejin         | 
| 腾讯新闻         | 热点榜       | qq-news        | 
| 新浪网           | 热榜         | sina           | 
| 新浪新闻         | 热点榜       | sina-news      | 
| 网易新闻         | 热点榜       | netease-news   | 
| 吾爱破解         | 榜单         | 52pojie        | 
| 全球主机交流     | 榜单         | hostloc        | 
| 虎嗅             | 24小时       | huxiu          | 
| 酷安             | 热榜         | coolapk        | 
| 虎扑             | 步行街热帖   | hupu           | 
| 爱范儿           | 快讯         | ifanr          | 
| 英雄联盟         | 更新公告     | lol            | 
| 米游社           | 最新消息     | miyoushe       | 
| 原神             | 最新消息     | genshin        | 
| 崩坏3            | 最新动态     | honkai         | 
| 崩坏：星穹铁道   | 最新动态     | starrail       | 
| 微信读书         | 飙升榜       | weread         | 
| NGA              | 热帖         | ngabbs         | 
| V2EX             | 主题榜       | v2ex           | 
| HelloGitHub      | Trending     | hellogithub    | 
| 中央气象台       | 全国气象预警 | weatheralarm   | 
| 中国地震台       | 地震速报     | earthquake     | 
| 历史上的今天     | 月-日        | history        |

请用中文撰写这篇总结。

{topics_text}

"""
    
    print(f"\n📝 完整提示词预览:\n{'-'*60}")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print(f"{'-'*60}\n")

    analysis_result = call_ollama(prompt, args.ollama_api, args.ollama_model,
                                  args.max_retries, args.retry_delay)

    if analysis_result:
        print("\n" + "="*60, flush=True)
        print("📊 分析结果", flush=True)
        print("="*60, flush=True)
        print(analysis_result, flush=True)
        print("\n" + "="*60, flush=True)

        os.makedirs(args.save_dir, exist_ok=True)
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "platforms_analyzed": list(all_topics.keys()),
            "raw_data": all_topics,
            "analysis": analysis_result
        }
        filename = os.path.join(args.save_dir,
                                f"hot_trends_analysis_{time.strftime('%Y%m%d_%H%M%S')}.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 分析结果已保存至: {filename}", flush=True)
    else:
        print("\n❌ Ollama分析失败，请检查Ollama服务是否正常运行", flush=True)


if __name__ == "__main__":
    print("="*60, flush=True)
    print("   网络热搜分析工具 - 命令行配置版", flush=True)
    print("="*60 + "\n", flush=True)

    args = parse_args()
    analyze_hot_trends(args)

    print("\n✨ 分析完成！", flush=True)