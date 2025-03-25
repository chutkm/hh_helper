# app/routes.py
from fastapi import APIRouter, Request, File, UploadFile, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing import db

from app.utils import extract_text_from_pdf, save_text_to_json, parse_resume
from app.models import process_embedding
import os
import json

from database.base import get_db
from database.request import add_candidate_to_db

#------------------------Маршруты API
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    db: AsyncSession = Depends(get_db)
    results = []
    for file in files:
        # Проверка расширения файла
        if not file.filename.lower().endswith('.pdf'):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Недопустимый формат файла. Разрешены только PDF."
            })
            continue

        try:
            # Сохранение файла
            file_path = os.path.join("uploads", file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Извлечение текста
            text = extract_text_from_pdf(file_path)

            # Сохранение текста в JSON
            json_output_path = os.path.join("uploads", f"{os.path.splitext(file.filename)[0]}.json")
            save_text_to_json(text, json_output_path)

            blocks = parse_resume(text)
            print(blocks)
            # # Добавление кандидата в базу данных
            # new_candidate = await add_candidate_to_db(db, blocks, text)


            # Создание эмбеддинга
            embedding_path = os.path.join("uploads", f"{file.filename}.json")
            embedding_result = process_embedding(text, embedding_path)

            results.append({
                "filename": file.filename,
                "status": "success",
                "message": "Текст успешно извлечен и обработан.",
                "text": text[:100] + "...",
                "embedding_path": embedding_path
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Ошибка: {str(e)}"
            })

    return {"results": results}