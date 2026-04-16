import pandas as pd
import random
from database import SessionLocal
from models import Movie

def import_movies_from_csv():
    # 1. 打开数据库会话
    db = SessionLocal()
    
    # 2. 读取我们刚爬好的 CSV 数据
    csv_file = 'douban_top250.csv'
    try:
        df = pd.read_csv(csv_file)
        print(f"成功读取 CSV 文件，共 {len(df)} 条记录。开始执行幂等导入...")
    except FileNotFoundError:
        print(f"找不到 {csv_file}，请确认文件是否在 backend 目录下！")
        return

    # 3. 准备前端需要的“情绪标签”池 
    emotions_pool = ['治愈', '搞笑', '致郁', '热血', '烧脑', '放松']

    added_count = 0
    updated_count = 0

    # 4. 遍历 CSV 里的每一行数据
    for index, row in df.iterrows():
        title_str = str(row['title'])
        director_cast_str = str(row['director_cast'])
        parts = director_cast_str.split("主演:")
        director = parts[0].replace("导演:", "").strip()
        cast = parts[1].strip() if len(parts) > 1 else "未知"
        
        emotion_tags = "|".join(random.sample(emotions_pool, k=random.randint(1, 2)))
        avg_rating = float(row['average_rating']) if pd.notna(row['average_rating']) else 0.0

        # 🌟 核心魔法：先去数据库里查，这部电影到底存不存在？
        existing_movie = db.query(Movie).filter(Movie.title == title_str).first()

        if existing_movie:
            # ✅ 如果存在，执行“覆盖更新” (Update)
            existing_movie.genres = str(row['genres'])
            existing_movie.director = director
            existing_movie.cast = cast
            existing_movie.description = str(row['description'])
            existing_movie.cover_url = str(row['cover_url'])
            existing_movie.average_rating = avg_rating
            # existing_movie.emotion_tags = emotion_tags # 如果你不想每次打乱已有的情绪标签，可以注释掉这行
            
            updated_count += 1
        else:
            # ✅ 如果不存在，执行“全新插入” (Insert)
            new_movie = Movie(
                title=title_str,
                genres=str(row['genres']),
                emotion_tags=emotion_tags,
                director=director,
                cast=cast,
                description=str(row['description']),
                cover_url=str(row['cover_url']),
                average_rating=avg_rating
            )
            db.add(new_movie)
            added_count += 1

    # 5. 提交保存到 SQLite 数据库中
    try:
        db.commit()
        print(f"🎉 导入任务完成！")
        print(f"📈 统计: 新增了 {added_count} 部电影，覆写更新了 {updated_count} 部电影。")
    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败，错误信息: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_movies_from_csv()