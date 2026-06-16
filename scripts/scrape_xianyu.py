"""
闲鱼搜索抓取工具
用法: python scrape_xianyu.py <关键词> [最大页数]
输出: JSON 格式的价格分布和商品列表
"""
import sys
import json
import re
from urllib.parse import quote

def build_search_url(keyword, page=1):
    """构建闲鱼搜索URL"""
    encoded = quote(keyword)
    return f"https://s.2.taobao.com/list/list.htm?q={encoded}&search_type=item&page={page}"

def parse_price(price_text):
    """从价格文本中提取数字"""
    if not price_text:
        return None
    match = re.search(r'[\d.]+', str(price_text).replace(',', ''))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def analyze_prices(items):
    """分析价格分布"""
    prices = [i['price'] for i in items if i.get('price') is not None]
    if not prices:
        return {"error": "无有效价格数据"}

    prices.sort()
    n = len(prices)
    avg_price = sum(prices) / n
    median_price = prices[n // 2]
    min_price = prices[0]
    max_price = prices[-1]

    # 价格区间分布
    if max_price - min_price == 0:
        ranges = {"全部": n}
    else:
        r1 = [p for p in prices if p <= avg_price * 0.5]
        r2 = [p for p in prices if avg_price * 0.5 < p <= avg_price * 1.5]
        r3 = [p for p in prices if avg_price * 1.5 < p <= avg_price * 2.5]
        r4 = [p for p in prices if p > avg_price * 2.5]
        ranges = {
            f"¥{min_price:.0f}-{avg_price*0.5:.0f}": len(r1),
            f"¥{avg_price*0.5:.0f}-{avg_price*1.5:.0f}": len(r2),
            f"¥{avg_price*1.5:.0f}-{avg_price*2.5:.0f}": len(r3),
            f"¥{avg_price*2.5:.0f}+": len(r4),
        }

    # 识别捡漏（价格低于均值 40% 以上）
    bargains = [
        i for i in items
        if i.get('price') and i['price'] < avg_price * 0.6 and i['price'] > 0
    ]
    bargains.sort(key=lambda x: x['price'])

    return {
        "total": n,
        "min": min_price,
        "max": max_price,
        "average": round(avg_price, 2),
        "median": round(median_price, 2),
        "distribution": ranges,
        "bargains": [{"title": b['title'], "price": b['price'], "link": b.get('link', '')} for b in bargains[:10]],
        "bargain_count": len(bargains),
    }

def format_for_openclaw(keyword, analysis):
    """生成 OpenClaw 可用的 Markdown 报告"""
    lines = [
        f"## 🐟 闲鱼搜品: 《{keyword}》",
        f"- 共 {analysis['total']} 个有效价格",
        f"- 最低价：¥{analysis['min']:.0f} | 最高价：¥{analysis['max']:.0f} | 中位数：¥{analysis['median']:.0f}",
    ]

    dist_parts = []
    for r, c in analysis['distribution'].items():
        pct = round(c / analysis['total'] * 100)
        dist_parts.append(f"{r} ({pct}%)")
    lines.append(f"- 📊 价格分布: {' | '.join(dist_parts)}")

    if analysis['bargains']:
        lines.append(f"\n### 🔍 捡漏候选: {analysis['bargain_count']} 个")
        for i, b in enumerate(analysis['bargains'][:5], 1):
            pct_off = round((1 - b['price'] / analysis['average']) * 100)
            lines.append(f"\n{i}. **[捡漏] {b['title']} ¥{b['price']:.0f}**")
            lines.append(f"   - 市场均价: ¥{analysis['average']:.0f} | 折扣: {pct_off}%")
            if b['link']:
                lines.append(f"   - 链接: {b['link']}")
    else:
        lines.append("\n⚠️ 未发现明显捡漏机会")

    # 推荐定价
    lines.append(f"\n### 🎯 推荐定价区间: ¥{analysis['average']*0.8:.0f} ~ ¥{analysis['average']*1.2:.0f}")

    print('\n'.join(lines))

if __name__ == '__main__':
    print("请通过 OpenClaw 调用此脚本，或使用 web_fetch 直接搜索闲鱼。")
    print("此脚本作为参考实现，实际抓取需要通过 OpenClaw 的 web_fetch 工具。")
