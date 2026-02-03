from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import create_db_and_tables

from app.routers import users



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
            ## Документ-центр API для ИП «Северный Контур»

            Внутренний веб-API сервис для управления документами по проектам.

            ### Возможности:
            - **Аутентификация** - JWT токены, bcrypt хеширование паролей
            - **Роли** - admin, manager, worker, viewer
            - **Проекты** - создание, редактирование, управление доступом
            - **Документы** - создание, редактирование, публикация, архивирование
            - **Версионирование** - автоматическое сохранение версий документов
            - **Аудит** - журнал всех действий пользователей

            ### Роли:
            - **admin** - полный доступ ко всем проектам и пользователям
            - **manager** - ведёт проекты, выдаёт доступ участникам своих проектов  
            - **worker** - читает и редактирует документы в рамках доступа "editor"
            - **viewer** - только чтение в рамках выданного доступа
    """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

def setup_cors_middleware():
    app.add_middleware(
        CORSMiddleware, 
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

@app.get("/", tags=["Root"])
def root():
    return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc"
        }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def main():
    setup_cors_middleware()

    app.include_router(users.router)


main()


