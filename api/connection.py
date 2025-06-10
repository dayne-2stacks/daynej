from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the base class for the ORM
Base = declarative_base()


# Define the UserMessage model
class Messages(Base):
    __tablename__ = "usermessage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    message = Column(String, nullable=False)


# Create the SQLite engine
DATABASE_URL = "sqlite:///usermessages.db"
engine = create_engine(DATABASE_URL, echo=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
