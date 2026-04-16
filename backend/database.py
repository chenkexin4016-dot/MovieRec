"""配置数据库连接"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 配置 SQLite 数据库文件路径
SQLALCHEMY_DATABASE_URL = "sqlite:///./movie_data.db"

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基本映射类（所有的表模型都要继承它）
Base = declarative_base()