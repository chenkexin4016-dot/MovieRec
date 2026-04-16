import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
import models
import random
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

def get_item_based_recommendations(db: Session, target_user_id: int, top_n: int = 8):
    """
    基于物品的协同过滤推荐算法 (Item-Based CF)
    """
    # 1. 从数据库中取出所有的评分数据
    ratings_query = db.query(models.Rating.user_id, models.Rating.movie_id, models.Rating.score).all()
    if not ratings_query:
        return [] # 数据库里完全没有打分记录，算法没法跑

    # 将数据转换为 Pandas DataFrame
    df = pd.DataFrame(ratings_query, columns=['user_id', 'movie_id', 'score'])

    # 2. 检查当前目标用户是否打过分 (处理冷启动问题)
    user_ratings = df[df['user_id'] == target_user_id]
    if user_ratings.empty:
        return [] # 该用户还没打过分，没法算相似度

    # 3. 构建核心矩阵：User-Item 评分矩阵 (Pivot Table)
    # 行是 movie_id，列是 user_id，值是打分。缺失值用 0 填充 (稀疏矩阵)
    movie_user_matrix = df.pivot_table(index='movie_id', columns='user_id', values='score').fillna(0)

    # 4. 计算物品相似度矩阵 (Cosine Similarity)
    # 算出来是一个对称矩阵，表示每一部电影和其他所有电影的相似度
    similarity_matrix = cosine_similarity(movie_user_matrix)
    similarity_df = pd.DataFrame(similarity_matrix, index=movie_user_matrix.index, columns=movie_user_matrix.index)

    # 5. 寻找推荐候选集
    # 找出该用户打过高分（>= 3.5星，即 7分以上）的电影
    liked_movies = user_ratings[user_ratings['score'] >= 7.0]['movie_id'].tolist()
    
    recommendation_scores = {}
    
    # 遍历用户喜欢的每一部电影，去相似度矩阵里找“邻居”
    for liked_movie_id in liked_movies:
        if liked_movie_id not in similarity_df.index:
            continue
            
        # 拿到与这部喜欢电影相似的其他电影列表
        similar_movies = similarity_df[liked_movie_id].sort_values(ascending=False)
        
        # 原始打分权重 (如果是 10分 权重就大，7分 权重就小)
        user_original_score = user_ratings[user_ratings['movie_id'] == liked_movie_id]['score'].values[0]
        
        for sim_movie_id, sim_score in similar_movies.items():
            # 必须排除掉用户自己本身已经看过的电影
            if sim_movie_id not in user_ratings['movie_id'].values:
                if sim_movie_id not in recommendation_scores:
                    recommendation_scores[sim_movie_id] = 0
                # 累加推荐得分：相似度 * 用户对基础电影的原始打分
                recommendation_scores[sim_movie_id] += (sim_score * user_original_score)

    # 6. 按最终计算的推荐得分排序，截取前 N 部
    sorted_recs = sorted(recommendation_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    recommended_movie_ids = [item[0] for item in sorted_recs]

    if not recommended_movie_ids:
        return []

    # 7. 拿着算出来的 ID 列表，去数据库查出完整的电影信息返回
    recommended_movies = db.query(models.Movie).filter(models.Movie.id.in_(recommended_movie_ids)).all()
    
    return recommended_movies

def get_popular_recommendations(db: Session, top_n: int = 8):
    """基线算法 1：全局热门推荐 (最高分)"""
    return db.query(models.Movie).order_by(models.Movie.average_rating.desc()).limit(top_n).all()

def get_random_recommendations(db: Session, top_n: int = 8):
    """基线算法 2：随机惊喜盲盒"""
    movies = db.query(models.Movie).all()
    if not movies:
        return []
    # 随机抽取 top_n 部电影
    return random.sample(movies, min(top_n, len(movies)))

def get_content_based_recommendations(db: Session, target_user_id: int, top_n: int = 8):
    """
    基于内容的 NLP 推荐算法 (Content-Based Filtering via TF-IDF)
    """
    # 1. 获取用户喜欢过的电影 (评分 >= 7.0 / 即 3.5 星以上)
    user_ratings = db.query(models.Rating).filter(
        models.Rating.user_id == target_user_id, 
        models.Rating.score >= 7.0
    ).all()
    
    if not user_ratings:
        return [] # 冷启动：用户还没打过高分
        
    liked_movie_ids = [r.movie_id for r in user_ratings]
    
    # 2. 获取全量电影数据
    all_movies = db.query(models.Movie).all()
    if not all_movies:
        return []
        
    # 3. 构建语料库 (Corpus) 与索引映射
    corpus = []
    movie_id_to_index = {}
    index_to_movie = {}
    
    for idx, m in enumerate(all_movies):
        # 将电影的 标题、类型、导演、演员、长简介 拼接成一段超级文本
        text = f"{m.title} {m.genres} {m.director or ''} {m.cast or ''} {m.description or ''}"
        
        # 使用 jieba 进行中文分词，用空格隔开
        words = " ".join(jieba.lcut(text))
        corpus.append(words)
        
        # 记录 ID 与矩阵索引的对应关系
        movie_id_to_index[m.id] = idx
        index_to_movie[idx] = m

    # 4. TF-IDF 向量化
    # 把文本转化为稀疏矩阵，屏蔽掉无意义的停用词特征
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(corpus)
    
    # 5. 计算相似度并打分
    recommendation_scores = {}
    
    for movie_id in liked_movie_ids:
        if movie_id not in movie_id_to_index:
            continue
            
        idx = movie_id_to_index[movie_id]
        
        # 使用 linear_kernel 计算当前电影与所有电影的余弦相似度 (TF-IDF矩阵归一化后，点乘即等于余弦相似度，计算更快)
        sim_scores = linear_kernel(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
        
        for sim_idx, score in enumerate(sim_scores):
            sim_movie_id = index_to_movie[sim_idx].id
            # 排除掉用户已经看过的电影
            if sim_movie_id not in liked_movie_ids:
                if sim_movie_id not in recommendation_scores:
                    recommendation_scores[sim_movie_id] = 0
                # 将相似度累加 (如果一部电影和用户喜欢的两部电影都很像，它的权重就会更高)
                recommendation_scores[sim_movie_id] += score
                
    # 6. 排序并返回 Top N
    sorted_recs = sorted(recommendation_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    # 按排序后的顺序提取完整的电影对象
    final_recommended_movies = []
    for item in sorted_recs:
        sim_movie_id = item[0]
        final_recommended_movies.append(next(m for m in all_movies if m.id == sim_movie_id))
        
    return final_recommended_movies