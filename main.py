from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from redis.asyncio import Redis
import os
import secrets

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/app.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
app = FastAPI(title="URL Shortener API")
redis_client: Optional[Redis] = None
Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String(2048), nullable=False)
    short_code = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    clicks = Column(Integer, default=0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None

class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    clicks: int
    owner_id: Optional[int]

class StatsOut(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime]

@app.on_event("startup")
async def startup():
    global redis_client
    Base.metadata.create_all(bind=engine)
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_short_code(length: int = 6) -> str:
    return secrets.token_urlsafe(length)[:length]

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_link_by_code(db: Session, short_code: str):
    return db.query(Link).filter(Link.short_code == short_code).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if not user:
        raise credentials_exception
    return user

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        return get_user_by_username(db, username)
    except Exception:
        return None


async def invalidate_link_cache(short_code: str):
    if redis_client:
        await redis_client.delete(f"link:{short_code}")
        await redis_client.delete(f"redirect:{short_code}")

@app.post("/auth/register", response_model=LinkOut | Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/links/shorten", response_model=LinkOut)
async def create_short_link(payload: LinkCreate, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    expires_at = payload.expires_at.replace(tzinfo=None) if payload.expires_at else None
    if expires_at and expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="expires_at must be in the future")
    if payload.custom_alias:
        existing = get_link_by_code(db, payload.custom_alias)
        if existing:
            raise HTTPException(status_code=400, detail="Custom alias already exists")
        short_code = payload.custom_alias
    else:
        short_code = generate_short_code()
        while get_link_by_code(db, short_code):
            short_code = generate_short_code()
    link = Link(
        original_url=str(payload.original_url),
        short_code=short_code,
        expires_at=expires_at,
        owner_id=current_user.id if current_user else None,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@app.get("/links/{short_code}", response_model=LinkOut)
async def get_link_info(short_code: str, db: Session = Depends(get_db)):
    cache_key = f"link:{short_code}"
    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)
    link = get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.expires_at and link.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link expired")
    data = LinkOut.model_validate(link).model_dump(mode="json")
    if redis_client:
        import json
        await redis_client.setex(cache_key, 300, json.dumps(data))
    return data

@app.get("/links/{short_code}/stats", response_model=StatsOut)
def get_link_stats(short_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {
        "short_code": link.short_code,
        "original_url": link.original_url,
        "clicks": link.clicks,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }

@app.get("/links/search", response_model=list[LinkOut])
def search_links(original_url: str, db: Session = Depends(get_db)):
    links = db.query(Link).filter(Link.original_url == original_url).all()
    return links


@app.put("/links/{short_code}", response_model=LinkOut)
async def update_link(short_code: str, payload: LinkUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if payload.original_url is not None:
        link.original_url = str(payload.original_url)
    if payload.expires_at is not None:
        if payload.expires_at.replace(tzinfo=None) <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="expires_at must be in the future")
        link.expires_at = payload.expires_at
    db.commit()
    db.refresh(link)
    await invalidate_link_cache(short_code)
    return link

@app.delete("/links/{short_code}")
async def delete_link(short_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    db.delete(link)
    db.commit()
    await invalidate_link_cache(short_code)
    return {"message": "Link deleted successfully"}

@app.get("/{short_code}")
async def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    cache_key = f"redirect:{short_code}"
    if redis_client:
        cached_url = await redis_client.get(cache_key)
        if cached_url:
            link = get_link_by_code(db, short_code)
            if link:
                link.clicks += 1
                db.commit()
            return RedirectResponse(url=cached_url, status_code=307)
    link = get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.expires_at and link.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link expired")
    link.clicks += 1
    db.commit()
    if redis_client:
        await redis_client.setex(cache_key, 300, link.original_url)
    return RedirectResponse(url=link.original_url, status_code=307)