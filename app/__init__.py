from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.routes import router
###---------------------Инициализация FastAPI приложения.
# Создание экземпляра FastAPI
app = FastAPI()
# Подключаем маршруты
app.include_router(router)
# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp_resumes", StaticFiles(directory="temp_resumes"), name="temp_resumes")
# # Инициализация модели SentenceTransformer
# model = SentenceTransformer('all-MiniLM-L6-v2')

# Создание папки для загрузок
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)