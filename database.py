# Kết nối cơ sở dữ liệu
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Đường dẫn lưu file database (SQLite)
# File này sẽ tự sinh ra cùng cấp với thư mục backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./app_oder.db"

# Khởi tạo engine để kết nối
# connect_args={"check_same_thread": False} chỉ dùng cho SQLite để chạy đa luồng
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Tạo SessionLocal: mỗi khi có request, ta sẽ mở một phiên làm việc (session) với DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: Lớp nền để các model (bảng) ở file models.py kế thừa
Base = declarative_base()

# Hàm (Dependency) để lấy database session cho mỗi request API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()