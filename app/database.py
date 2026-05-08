 # Corrected: create_engine
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from .models import Base


# # This creates a file named 'gidr.db' in your root folder
# SQLALCHEMY_DATABASE_URL = "sqlite:///./gidr.db"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# def init_db():
#     Base.metadata.create_all(bind=engine)

# # Dependency to get a database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()