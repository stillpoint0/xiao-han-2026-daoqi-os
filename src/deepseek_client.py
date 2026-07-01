import os
import json
from pathlib import Path
import urllib.request
import urllib.error

# 加载 .env
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

load_env()


API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def call_deepseek(model: str, messages: list, temperature: float = 0.6, timeout: int = 120) -> dict:
    """调用 DeepSeek API，返回完整响应字典。使用标准库 urllib，无需 requests。"""
    if not API_KEY:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY")
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    print(f"BASE_URL: {BASE_URL}")
    print(f"API_KEY length: {len(API_KEY) if API_KEY else 0}")
    try:
        result = call_deepseek(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "你好，请用一句话确认 API 连通。"}],
        )
        content = result["choices"][0]["message"]["content"]
        print("连通成功，模型返回:")
        print(content)
    except Exception as e:
        print(f"连通失败: {e}")
