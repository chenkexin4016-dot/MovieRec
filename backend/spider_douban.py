import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import traceback

def fetch_douban_top250():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    movies_data = []
    print("开始爬取豆瓣电影 Top 250...\n")
    
    for i in range(0, 250, 25): 
        url = f'https://movie.douban.com/top250?start={i}'
        print(f"正在抓取第 {i//25 + 1} 页: {url}")
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='item')
        
        if not items:
            print("警告：本页没有找到任何电影，可能是被豆瓣反爬拦截了！请停止尝试，稍后再试。")
            break

        for item in items:
            try:
                # 1. 电影名
                title = item.find('span', class_='title').text
                
                # 2. 海报链接
                cover_url = item.find('img')['src']
                
                # 3. 评分
                rating = item.find('span', class_='rating_num').text
                
                # 4. 导演、主演、类型
                # 不再强求 class_=''，直接找 bd 下面的第一个 p 标签，这样最稳妥！
                info_p_tag = item.find('div', class_='bd').find('p')
                info_text = info_p_tag.text.strip() if info_p_tag else ""
                info_parts = info_text.split('\n')
                
                crew_info = info_parts[0].strip() if len(info_parts) > 0 else "暂无演职人员信息"
                meta_info = info_parts[1].strip() if len(info_parts) > 1 else ""
                
                genres = meta_info.split('/')[-1].strip().replace(' ', '|') if meta_info else ""
                
                # 5. 一句话简介
                quote_tag = item.find('span', class_='inq')
                description = quote_tag.text if quote_tag else "暂无简介"
                
                movies_data.append({
                    'title': title,
                    'genres': genres,
                    'director_cast': crew_info,
                    'average_rating': float(rating),
                    'description': description,
                    'cover_url': cover_url
                })
            except Exception as e:
                # 如果再报错，打印出具体的错误类型和出错的电影 HTML，方便我们排查
                print(f"解析电影出错: {e}")
                print(traceback.format_exc())
                continue
                
        time.sleep(random.uniform(1, 3))
        
    df = pd.DataFrame(movies_data)
    csv_filename = 'douban_top250.csv'
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"\n 爬取大功告成！共抓取 {len(movies_data)} 条数据，已保存至 {csv_filename}")

if __name__ == '__main__':
    fetch_douban_top250()