from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DB_CONFIG  # Đảm bảo bạn có file config.py

# Cấu hình kết nối MySQL sử dụng mysql-connector
DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# Tạo engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Đổi thành True nếu bạn muốn log truy vấn
    pool_pre_ping=True,
)

# Tạo session dùng để thao tác với DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Khởi tạo base class để khai báo models
Base = declarative_base()
