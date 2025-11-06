import feedparser
import yaml

# 加载配置
with open('config/sources.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("测试RSS源可用性\n" + "="*60)

# 排除Bloomberg和CNBC
exclude_sources = ["Bloomberg Markets", "CNBC Top News"]

for source in config['rss_sources']:
    if source['name'] in exclude_sources:
        print(f"\n⏭️  跳过: {source['name']}")
        continue
    
    print(f"\n📡 测试: {source['name']}")
    print(f"   URL: {source['url']}")
    
    try:
        feed = feedparser.parse(source['url'])
        
        if feed.bozo:
            print(f"   ❌ 解析错误: {feed.bozo_exception}")
            continue
        
        if not feed.entries:
            print(f"   ⚠️  无内容")
            continue
        
        print(f"   ✅ 成功! 获取到 {len(feed.entries)} 条")
        
        # 显示前3条标题
        for i, entry in enumerate(feed.entries[:3], 1):
            title = entry.get('title', 'No title')[:60]
            print(f"      {i}. {title}")
    
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:50]}")

print("\n" + "="*60)
print("测试完成")
