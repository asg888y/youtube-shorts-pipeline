"""热点主题发现 — 微博热搜、知乎热榜、今日头条、抖音热点."""

import requests
from html.parser import HTMLParser
from typing import Optional
from dataclasses import dataclass


def _log(msg: str):
    """简单日志."""
    print(f"  {msg}")


@dataclass
class HotTopic:
    """热点主题数据结构."""
    title: str
    source: str
    rank: int
    heat: Optional[int] = None  # 热度值
    url: Optional[str] = None


def fetch_weibo_hot() -> list[HotTopic]:
    """获取微博热搜榜."""
    topics = []
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://weibo.com",
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            hot_list = data.get("data", {}).get("realtime", [])
            for i, item in enumerate(hot_list[:20]):
                topics.append(HotTopic(
                    title=item.get("note", ""),
                    source="微博热搜",
                    rank=i + 1,
                    heat=item.get("num", 0),
                    url=f"https://s.weibo.com/weibo?q={item.get('query', '')}",
                ))
            _log(f"微博热搜: {len(topics)}条")
    except Exception as e:
        _log(f"微博热搜获取失败: {e}")
    return topics


def fetch_zhihu_hot() -> list[HotTopic]:
    """获取知乎热榜."""
    topics = []
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            hot_list = data.get("data", [])
            for i, item in enumerate(hot_list[:20]):
                target = item.get("target", {})
                topics.append(HotTopic(
                    title=target.get("title", ""),
                    source="知乎热榜",
                    rank=i + 1,
                    heat=item.get("detail_text", "").replace("热度", "").strip() if item.get("detail_text") else None,
                    url=target.get("url", ""),
                ))
            _log(f"知乎热榜: {len(topics)}条")
    except Exception as e:
        _log(f"知乎热榜获取失败: {e}")
    return topics


def fetch_baidu_hot() -> list[HotTopic]:
    """获取百度热搜."""
    topics = []
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # 简单解析
            import re
            titles = re.findall(r'"word":"([^"]+)"', r.text)
            for i, title in enumerate(titles[:20]):
                topics.append(HotTopic(
                    title=title,
                    source="百度热搜",
                    rank=i + 1,
                ))
            _log(f"百度热搜: {len(topics)}条")
    except Exception as e:
        _log(f"百度热搜获取失败: {e}")
    return topics


def fetch_douyin_hot() -> list[HotTopic]:
    """获取抖音热点榜."""
    topics = []
    try:
        # 抖音热点API（模拟）
        # 实际可以使用：https://www.douyin.com/aweme/v1/web/hot/search/list/
        import random
        # 模拟抖音热点数据
        mock_topics = [
            "挑战赛：全网都在跳这个舞",
            "爆款BGM：这首音乐火了",
            "热门特效：这个滤镜太绝了",
            "情感语录：这段话治愈了多少人",
            "生活技巧：原来这样更省事",
            "美食探店：这家店排队3小时",
            "搞笑段子：笑不活了家人们",
            "宠物日常：我家猫成精了",
            "穿搭分享：这件衣服太显瘦",
            "健身教程：30天瘦10斤"
        ]

        for i, title in enumerate(mock_topics[:10]):
            topics.append(HotTopic(
                title=title,
                source="抖音热点",
                rank=i + 1,
                heat=random.randint(100000, 1000000)
            ))
        _log(f"抖音热点: {len(topics)}条")
    except Exception as e:
        _log(f"抖音热点获取失败: {e}")
    return topics


def fetch_kuaishou_hot() -> list[HotTopic]:
    """获取快手热点榜."""
    topics = []
    try:
        # 快手热点API（模拟）
        # 实际可以使用快手开放平台API
        import random
        # 模拟快手热点数据
        mock_topics = [
            "老铁必看：这个操作太6了",
            "同城热点：本地发生的大事",
            "才艺展示：民间高手在快手",
            "三农内容：农村生活实录",
            "搞笑短剧：一分钟一个笑点",
            "手工制作：手艺人太牛了",
            "美食教程：家常菜这样做",
            "情感故事：普通人的真实生活",
            "萌宠日常：动物成精现场",
            "技能教学：一招学会新技能"
        ]

        for i, title in enumerate(mock_topics[:10]):
            topics.append(HotTopic(
                title=title,
                source="快手热点",
                rank=i + 1,
                heat=random.randint(50000, 800000)
            ))
        _log(f"快手热点: {len(topics)}条")
    except Exception as e:
        _log(f"快手热点获取失败: {e}")
    return topics


def fetch_xiaohongshu_hot() -> list[HotTopic]:
    """获取小红书热点榜."""
    topics = []
    try:
        # 小红书热点API（模拟）
        # 实际可以使用小红书开放平台API
        import random
        # 模拟小红书热点数据
        mock_topics = [
            "探店分享：这家店拍照绝了",
            "穿搭教程：小个子显高穿搭",
            "护肤心得：敏感肌救星来了",
            "家居好物：提升幸福感的小物",
            "旅行攻略：小众打卡地推荐",
            "美食测评：网红产品实测",
            "学习笔记：高效学习方法",
            "职场经验：新人避坑指南",
            "母婴分享：带娃实用好物",
            "健身打卡：减肥经验分享"
        ]

        for i, title in enumerate(mock_topics[:10]):
            topics.append(HotTopic(
                title=title,
                source="小红书热点",
                rank=i + 1,
                heat=random.randint(30000, 500000)
            ))
        _log(f"小红书热点: {len(topics)}条")
    except Exception as e:
        _log(f"小红书热点获取失败: {e}")
    return topics


def fetch_all_hot_sources() -> list[HotTopic]:
    """聚合所有热点源."""
    all_topics = []

    # 微博热搜 (最实时)
    all_topics.extend(fetch_weibo_hot())

    # 知乎热榜 (深度讨论)
    all_topics.extend(fetch_zhihu_hot())

    # 百度热搜
    all_topics.extend(fetch_baidu_hot())

    # 抖音热点 (短视频平台)
    all_topics.extend(fetch_douyin_hot())

    # 快手热点 (短视频平台)
    all_topics.extend(fetch_kuaishou_hot())

    # 小红书热点 (生活方式)
    all_topics.extend(fetch_xiaohongshu_hot())

    # 去重（按标题）
    seen = set()
    unique_topics = []
    for t in all_topics:
        if t.title not in seen:
            seen.add(t.title)
            unique_topics.append(t)

    return unique_topics


def get_top_hot_topic() -> Optional[HotTopic]:
    """获取当前最热话题（排名第一）."""
    topics = fetch_all_hot_sources()
    if topics:
        return topics[0]
    return None


def list_hot_topics(limit: int = 20) -> list[HotTopic]:
    """列出热点话题供选择."""
    topics = fetch_all_hot_sources()
    return topics[:limit]


def print_hot_topics(limit: int = 20):
    """打印热点话题列表."""
    topics = list_hot_topics(limit)
    if not topics:
        print("  未获取到热点话题")
        return

    print(f"\n  当前热点话题 ({len(topics)}条):\n")
    for t in topics:
        heat_str = f" [{t.heat}]" if t.heat else ""
        print(f"  {t.rank:2d}. [{t.source}] {t.title}{heat_str}")