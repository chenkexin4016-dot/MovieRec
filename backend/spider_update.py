import requests
from bs4 import BeautifulSoup
import time
import random
from database import SessionLocal
import models

def update_movie_descriptions():
    # 1. 开启数据库会话
    db = SessionLocal()
    
    # 2. 终极伪装：全套真实浏览器参数 + 你的 VIP 专属 Cookie 🔑
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Host": "movie.douban.com",
        "Connection": "keep-alive",
        "Cookie": 'll="118254"; bid=kA7ZICQTNHU; ap_v=0,6.0; _vwo_uuid_v2=D2E1088D4667BA44F6C41276BDBBF7981|cf23c060ffca06655dc4de265d3c4024; dbcl2="271704462:s4L4xO9ejqA"; ck=qiMe; push_noty_num=0; push_doumail_num=0; frodotk_db="00c2687833ea755a024739689bbf600e"'
    }

    print("🚀 开始执行深度潜入任务：更新电影长简介...")
    
    try:
        # 3. 遍历 Top 250 的 10 页列表
        for i in range(0, 250, 25):
            list_url = f"https://movie.douban.com/top250?start={i}&filter="
            print(f"\n📁 正在解析列表页: 第 {i//25 + 1} 页")
            
            try:
                res = requests.get(list_url, headers=headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('div', class_='item')

                for item in items:
                    title = item.find('span', class_='title').text
                    detail_url = item.find('a')['href'] 

                    # 去数据库里找这部电影
                    movie = db.query(models.Movie).filter(models.Movie.title == title).first()
                    if not movie:
                        continue
                    
                    # 如果简介长度超过 50 个字，说明已经爬过长简介了，节约弹药直接跳过
                    if movie.description and len(movie.description) > 50:
                        print(f"⏩ [{title}] 已有长简介，跳过...")
                        continue

                    print(f"🕵️‍♂️ 正在潜入 [{title}] 的详情页...")
                    
                    # 4. 核心：请求详情页
                    detail_res = requests.get(detail_url, headers=headers)
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    
                    # 🚨 侦察代码：检查是否被拦截
                    page_title = detail_soup.title.text.strip() if detail_soup.title else "未知页面"
                    if "登录" in page_title or "验证" in page_title:
                        print(f"❌ 警告！触发反爬机制，当前页面是: {page_title}")
                        print("🛑 任务强制终止，请稍后再试或更新 Cookie。")
                        return # 立即退出函数，防止 IP 被封禁
                    
                    # 寻找包含剧情简介的 span 标签
                    summary_span = detail_soup.find('span', property='v:summary')
                    
                    if summary_span:
                        # 获取文本，清除多余的空格和换行
                        long_desc = summary_span.text.strip().replace('\n', '').replace('　　', '')
                        
                        # 5. 更新写入数据库
                        movie.description = long_desc
                        db.commit()
                        print(f"✅ 成功获取 [{title}] 简介！字数: {len(long_desc)}")
                    else:
                        print(f"⚠️ 未能找到 [{title}] 的简介标签。页面标题: {page_title}")

                    # 6. 极其关键：随机休眠 2~5 秒，模拟人类真实点击节奏！
                    sleep_time = random.uniform(2, 5)
                    time.sleep(sleep_time)

            except Exception as e:
                print(f"⚠️ 爬取当前页发生意外错误: {e}")
                print("休眠 10 秒后继续...")
                time.sleep(10)

    finally:
        # 确保无论发生什么，最后都会安全关闭数据库连接
        db.close()
        print("\n🎉 潜入任务结束！数据库连接已安全断开。")

if __name__ == "__main__":
    update_movie_descriptions()