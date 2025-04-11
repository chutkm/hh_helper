# app/routes.py
from fastapi import APIRouter, Request, File, UploadFile, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing import db

from app.utils import extract_text_from_pdf, save_text_to_json, parse_resume, \
    extract_entities, lemmatize_text, clean_text, tokenize_text, create_vector, \
    process_contact_info, process_personal_info, \
    process_skills, extract_english_level, load_universities
from app.models import process_embedding
import os
import json

from database.request import DatabaseHandler

#------------------------Маршруты API
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

from threading import Thread

from threading import Thread

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    results = []
    db_handler = DatabaseHandler()
    threads = []

    def process_file(file):
        try:
            # Проверка расширения файла
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Недопустимый формат файла. Разрешены только PDF."
                })
                return

            # Сохранение файла (синхронное чтение)
            file_path = os.path.join("uploads", file.filename)
            with open(file_path, "wb") as f:
                f.write(file.file.read())  # Синхронное чтение вместо await file.read()

            # Извлечение текста
            text = extract_text_from_pdf(file_path)

            # Обработка данных
            person = process_personal_info(text)

            phone_email = process_contact_info(text)
            print("кандидат :", phone_email)
            skills = process_skills(text)
            english = extract_english_level(text)

            # Разбор контактов
            phone = phone_email.get('phone', '').strip()
            email = phone_email.get('email', '').strip()

            # Подготовка данных для вставки
            candidate_data = {
                "full_name": person.get('name', ''),  # ФИО
                "phone": phone,  # Телефон
                "email": email,  # Почта
                "skills": skills,  # Навыки (массив строк)
                "english_level": english,  # Уровень английского
                "education": "",  # Пустое поле для образования
                "work_experience": ""  # Пустое поле для опыта работы
            }
            #Текст с резюме
            # Сохранение текста в JSON
            json_output_path = os.path.join("uploads", f"{os.path.splitext(file.filename)[0]}.json")
            save_text_to_json(text, json_output_path)

            # Вставка данных в таблицу candidates вместе с PDF-файлом
            db_handler.insert_candidate(candidate_data, file_path)
            #
            # # Создание эмбеддинга
            # embedding_path = os.path.join("uploads", f"{file.filename}.json")
            # embedding_result = process_embedding(text, embedding_path)

            # Добавление результата
            results.append({
                "filename": file.filename,
                "status": "success",
                "message": "Текст успешно извлечен и обработан.",
                "text": text[:100] + "..."

            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Ошибка: {str(e)}"
            })

    # Запуск потоков для обработки файлов
    for file in files:
        thread = Thread(target=process_file, args=(file,))
        threads.append(thread)
        thread.start()

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()

    # Закрытие соединения с базой данных
    db_handler.close_connection()

    return {"results": results}


@router.post("/add_position")
async def add_position(position_data: dict):
    try:
        # Создаем объект для работы с базой данных
        db_handler = DatabaseHandler()

        # Добавляем данные в базу
        db_handler.insert_position(position_data)

        return {"message": "Данные успешно добавлены в базу данных!"}
    except Exception as e:
        return {"error": str(e)}, 500
@router.get("/ranking")
async def show_ranking(request: Request, position: str = ""):
    return templates.TemplateResponse(
        "ranking.html",
        {
            "request": request,
            "position": position
        }
    )
