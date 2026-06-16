#!/usr/bin/env python3
"""
xianyu_scout.py - 闲鱼搜品 + 捡漏识别（使用 mtop API）
用法：python scrape_xianyu.py <关键词> [--min-price 0] [--max-price 99999]
"""

import sys
import json
import time
import random
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

# 闲鱼 mtop API 端点
MTOP_URL = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemode.pc.search/1.0/"

# 模拟移动端 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.xianyu.com/",
    "Origin": "https://www.xianyu.com",
}

def build_mtop_params(keyword, page=1, page_size=20):
    """构建 mtop 请求参数"""
    data = {
        "q": keyword,
        "searchType": "SELL",
        "pageNo": page,
        "pageSize": page_size,
        "sortType": "TIME_DESC",  # 按时间倒序
    }
    return data

def fetch_xianyu(keyword, min_price=0, max_price=99999, max_pages=3):
    """
    抓取闲鱼商品数据
    返回：[{title, price, seller, url, publish_time}, ...]
    """
    results = []
    
    for page in range(1, max_pages + 1):
        print(f"[*] 正在抓取第 {page} 页...", file=sys.stderr)
        
        params = build_mtop_params(keyword, page)
        url = f"{MTOP_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
                data = json.loads(content)
                
                # 解析商品列表
                items = data.get("data", {}).get("items", [])
                if not items:
                    print(f"[!] 第 {page} 页无数据，可能被限流", file=sys.stderr)
                    break
                
                for item in items:
                    price = float(item.get("price", 0))
                    if min_price <= price <= max_price:
                        results.append({
                            "title": item.get("title", ""),
                            "price": price,
                            "seller": item.get("seller", {}).get("name", "未知"),
                            "url": f"https://www.xianyu.com/item/{item.get('itemId', '')}",
                            "publish_time": item.get("publishTime", ""),
                            "status": item.get("status", ""),
                        })
                
                # 随机延迟，避免被封
                time.sleep(random.uniform(1.5, 3.0))
                
        except Exception as e:
            print(f"[!] 抓取第 {page} 页失败: {e}", file=sys.stderr)
            break
    
    return results

def analyze_prices(items):
    """分析价格分布，识别捡漏机会"""
    if not items:
        return {"error": "无商品数据"}
    
    prices = [i["price"] for i in items]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    # 捡漏：低于平均价 20%
    deal_threshold = avg_price * 0.8
    deals = [i for i in items if i["price"] < deal_threshold]
    
    return {
        "total": len(items),
        "avg_price": round(avg_price, 2),
        "min_price": min_price,
        "max_price": max_price,
        "deals": deals,
        "deal_count": len(deals),
    }

def main():
    parser = argparse.ArgumentParser(description="闲鱼搜品 + 捡漏识别")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--min-price", type=float, default=0, help="最低价格")
    parser.add_argument("--max-price", type=float, default=99999, help="最高价格")
    parser.add_argument("--pages", type=int, default=3, help="抓取页数")
    parser.add_argument("--output", help="输出 JSON 文件路径")
    args = parser.parse_args()
    
    print(f"[*] 搜索关键词: {args.keyword}", file=sys.stderr)
    items = fetch_xianyu(args.keyword, args.min_price, args.max_price, args.pages)
    
    if not items:
        print(json.dumps({"error": "未抓取到商品，可能被反爬限制"}, ensure_ascii=False))
        return
    
    analysis = analyze_prices(items)
    
    result = {
        "keyword": args.keyword,
        "fetch_time": datetime.now().isoformat(),
        "items": items,
        "analysis": analysis,
    }
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[*] 结果已保存到 {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
