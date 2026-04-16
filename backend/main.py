from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from pydantic import BaseModel

# ==========================================
# 导入数据库配置、表模型、推荐算法
# ==========================================
from database import SessionLocal, engine
import models
from recommender import get_item_based_recommendations, get_popular_recommendations, get_random_recommendations, get_content_based_recommendations

# 告诉 SQLAlchemy：去 models.py 里把所有的表给我建出来！
models.Base.metadata.create_all(bind=engine)

# ==========================================
# 1. 安全与加密配置 (JWT 设置)
# ==========================================
SECRET_KEY = "your_super_secret_key_here" # 密钥，生产环境中应该放在环境变量里
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token 有效期设为 24 小时

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login") # 告诉系统去哪里获取登录 token

# 密码加密与验证工具函数
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================================
# 2. Pydantic 数据验证模型 (规范前端传来的数据)
# ==========================================
class UserCreate(BaseModel):
    username: str
    password: str

# ==========================================
# 3. FastAPI 应用与中间件配置
# ==========================================
app = FastAPI()

# 解决跨域问题，允许 Vue 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. 路由接口 (Endpoints)
# ==========================================

# 测试接口
@app.get("/")
def read_root():
    return {"message": "电影推荐系统 API 已启动！请访问 /docs 查看接口文档"}

# 接口一：用户注册
@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. 检查用户名是否已存在
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已被注册")
    
    # 2. 密码加密并保存到数据库
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "注册成功", "username": new_user.username}

# 接口二：用户登录 (获取 Token)
@app.post("/api/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. 验证用户是否存在
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    # 2. 验证密码是否正确
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. 验证通过，签发 JWT Token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 接口三：获取当前登录用户信息 (测试 Token 是否有效)
@app.get("/api/users/me")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # 解析前端传来的 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的凭证")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的凭证或 Token 已过期")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="未找到用户")
    
    return {"id": user.id, "username": user.username, "role": user.role}

@app.get("/api/movies")
def get_movies(emotion: str = None, query: str = None, db: Session = Depends(get_db)):
    # 开始构建查询
    db_query = db.query(models.Movie)
    
    # 1. 如果有情绪标签过滤
    if emotion:
        db_query = db_query.filter(models.Movie.emotion_tags.like(f"%{emotion}%"))
    
    # 2. 如果有关键词搜索 (新增逻辑)
    if query:
        # 同时匹配电影名 or 类型，只要有一个包含关键词就搜出来
        db_query = db_query.filter(
            (models.Movie.title.contains(query)) | 
            (models.Movie.genres.contains(query))
        )
    
    # 3. 执行查询，限制前 50 部
    movies = db_query.limit(50).all()
    
    # 4. 格式化返回
    result = []
    for m in movies:
        result.append({
            "id": m.id,
            "title": m.title,
            "genres": m.genres,
            "emotion": m.emotion_tags,
            "rating": m.average_rating,
            "cover_url": m.cover_url,
            "director": m.director,
            "cast": m.cast,
            "description": m.description
        })
    return result

# ==========================================
# 新增：用户提交电影打分的接口
# ==========================================

# 1. 定义前端传过来的打分数据格式
class RatingCreate(BaseModel):
    movie_id: int
    score: float
    comment: str = "" # 短评暂时可选

@app.post("/api/rate")
def rate_movie(rating_data: RatingCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 1. 解析 Token，看看是谁在打分
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="请先登录后再打分！")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="未找到该用户")

    # 2. 检查这个用户之前是不是给这部电影打过分了
    existing_rating = db.query(models.Rating).filter(
        models.Rating.user_id == user.id,
        models.Rating.movie_id == rating_data.movie_id
    ).first()

    if existing_rating:
        # 如果打过分了，就更新分数
        existing_rating.score = rating_data.score
        existing_rating.comment = rating_data.comment
        db.commit()
        return {"message": "评分更新成功！"}
    else:
        # 如果没打过分，就新建一条打分记录
        new_rating = models.Rating(
            user_id=user.id,
            movie_id=rating_data.movie_id,
            score=rating_data.score,
            comment=rating_data.comment
        )
        db.add(new_rating)
        db.commit()
        return {"message": "评分提交成功！"}

# ==========================================
# 新增：获取当前用户所有评分/评论历史的接口 (用户中心用)
# ==========================================
@app.get("/api/user/ratings")
def get_user_ratings_history(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 1. 验证用户身份
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="凭证无效")
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 2. 核心魔法：使用 Join（关联查询）
    # 我们查的是 Rating 表，但同时要把关联的 Movie 表数据也拿出来
    # 这样我们才能知道评分对应的电影海报
    user_ratings = db.query(models.Rating).filter(models.Rating.user_id == user.id).all()

    # 3. 格式化数据吐给前端
    result = []
    for r in user_ratings:
        # 通过 models.py 里定义的 relationship，r.movie 就能直接拿到电影信息
        movie = r.movie
        result.append({
            "movie_id": movie.id,
            "movie_title": movie.title,
            "cover_url": movie.cover_url, # 海报不能丢
            "user_score": r.score / 2, # 核心：将数据库的 10分制转回前端的 5星制
            "comment": r.comment or "暂无评论", # 预留评论字段
            "rated_at": r.created_at.strftime("%Y-%m-%d %H:%M") # 格式化时间
        })
    return result

# ==========================================
# 升级版：支持多路策略的推荐接口
# ==========================================
@app.get("/api/recommend")
def get_personalized_recommendations(algo: str = "content_based", token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 1. 验证用户身份
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="凭证无效")
        
    user = db.query(models.User).filter(models.User.username == username).first()
    
    # 2. 策略路由 (Strategy Routing)：根据前端传来的 algo 选择算法
    if algo == "item_cf":
        recommended_movies = get_item_based_recommendations(db, target_user_id=user.id, top_n=8)
        # 如果协同过滤没算出结果（冷启动），用热门兜底
        if not recommended_movies:
            recommended_movies = get_popular_recommendations(db, 8)
    # 2. 策略路由 (Strategy Routing)：根据前端传来的 algo 选择算法
    if algo == "item_cf":
        recommended_movies = get_item_based_recommendations(db, target_user_id=user.id, top_n=8)
        if not recommended_movies:
            recommended_movies = get_popular_recommendations(db, 8)
    elif algo == "content_based":
        recommended_movies = get_content_based_recommendations(db, target_user_id=user.id, top_n=8)
        if not recommended_movies:
            recommended_movies = get_popular_recommendations(db, 8)          
    elif algo == "popular":
        recommended_movies = get_popular_recommendations(db, 8)
    elif algo == "random":
        recommended_movies = get_random_recommendations(db, 8)
    else:
        recommended_movies = get_popular_recommendations(db, 8)
        
    # 3. 格式化返回给前端 (记得带上咱们之前加的导演、演员、简介字段)
    result = []
    for m in recommended_movies:
        result.append({
            "id": m.id, "title": m.title, "genres": m.genres,
            "emotion": m.emotion_tags, "rating": m.average_rating, "cover_url": m.cover_url,
            "director": m.director, "cast": m.cast, "description": m.description
        })
    return result