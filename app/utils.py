from pathlib import Path

from PyPDF2 import PdfReader
import json
import re
from typing import Dict
import spacy
from typing import List
import requests
from spacy.matcher import PhraseMatcher

# from sentence_transformers import SentenceTransformer
# from spacy.matcher import PhraseMatcher
# from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

#-----------------------------Вспомогательные функции для работы с PDF.
# Загрузка модели spaCy для русского языка
nlp = spacy.load("ru_core_news_lg")


# # Инициализация модели SentenceTransformer
# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

#Очистка текста: удаляет лишние символы и приводит к нижнему регистру
def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)  # Удаляем знаки препинания
    text = text.lower()  # Приводим к нижнему регистру
    return text

#Токенизация текста (на слова)
def tokenize_text(text):
    doc = nlp(text)
    tokens = [token.text for token in doc]
    return tokens

#Лемматизация текста: приводит слова к базовой форме
def lemmatize_text(text):
    doc = nlp(text)
    lemmas = [token.lemma_ for token in doc]
    return lemmas

#Извлечение сущностей (NER) (компании, даты)
def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

#Создание векторного представления текста
# def create_vector(text):
#     vector = embedding_model.encode(text)
#     return vector
#--------------------------------------------------------------------



#----------------------------------------------------------------------
#извлечение текста с pdf
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    #     # Удаляем служебные символы
    # cleaned_text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
    #
    # # Убираем лишние пробелы и переносы строк
    # cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        # Убираем символы переноса строки (\n)
    # cleaned_text = text.replace("\n", " ").strip()
    # cleaned_text = text.replace("\xa", " ").strip()
    return text


# Функция для сохранения текста в JSON
# def save_text_to_json(text, output_path):
#     try:
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump({"text": text}, f, ensure_ascii=False, indent=4)
#     except Exception as e:
#         raise IOError(f"Ошибка при записи JSON: {e}")


def save_text_to_json(text, output_path):
    try:
        # Очистка текста от лишних пробелов, табуляций и переносов строк
        def clean_text(input_text):
            # Удаляем лишние пробелы и табуляции между словами
            input_text = re.sub(r'\s+', ' ', input_text)
            # Удаляем пробелы в начале и конце строки
            input_text = input_text.strip()
            return input_text

        # Очищаем текст
        cleaned_text = clean_text(text)

        # Сохраняем очищенный текст в JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"text": cleaned_text}, f, ensure_ascii=False, indent=4)

    except Exception as e:
        raise IOError(f"Ошибка при записи JSON: {e}")

#----------------------------Предобработка текста


def parse_resume(text):
    blocks = {}

    # Разбиение текста на блоки с помощью регулярных выражений
    def extract_block(pattern, text):
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    # Контактная информация
    contact_info = extract_block(r"(?i)(?:контакты|contact info):\s*(.*?)(\n\n|\Z)", text)
    if contact_info:
        blocks["contact_info"] = process_contact_info(contact_info)

    # Личная информация
    personal_info = extract_block(r"(?i)(?:личная информация|personal info):\s*(.*?)(\n\n|\Z)", text)
    if personal_info:
        blocks["personal_info"] = process_personal_info(personal_info)



    # Курсы и тренинги
    courses = extract_block(r"(?i)(?:курсы и тренинги|courses and training|Professional development):\s*(.*?)(\n\n|\Z)", text)
    if courses:
        blocks["courses"] = courses.strip()

    # Проекты
    projects = extract_block(r"(?i)(?:проекты|pet-project):\s*(.*?)(\n\n|\Z)", text)
    if projects:
        blocks["projects"] = projects.strip()

    # Навыки
    skills = extract_block(r"(?i)(?:навыки|skills|технические навыки|stack|Technical Skills):\s*(.*?)(\n\n|\Z)", text)
    if skills:
        blocks["skills"] = process_skills(skills)

    # Личные качества
    qualities = extract_block(r"(?i)(?:личные качества|personal qualities):\s*(.*?)(\n\n|\Z)", text)
    if qualities:
        blocks["qualities"] = qualities.strip()

    return blocks


#--------------------------ПОЧТА И ТЕЛЕФОН

def process_contact_info(contact_block):
    """Извлечение данных из блока контактов."""
    doc = nlp(contact_block)
    phone = None
    email = None

    for ent in doc.ents:
        if ent.label_ == "PHONE":
            phone = ent.text
        elif ent.label_ == "EMAIL":
            email = ent.text

    # Если spaCy не распознал, используем регулярные выражения
    if not phone:
        phone_match = re.search(r"\+?\d[\d\s()-]{7,15}", contact_block)
        phone = phone_match.group(0) if phone_match else None

    if not email:
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", contact_block)
        email = email_match.group(0) if email_match else None

    return {"phone": phone, "email": email}


#------------------------ИМЯ И ФАМИЛИЯ
def process_personal_info(personal_block):
    # Очищаем текст
    personal_block = personal_block.strip()

    # Извлекаем сущности через spaCy
    entities = extract_entities(personal_block)

    # Фильтруем сущности, оставляя только PER (имена и фамилии)
    name_parts = []
    for ent in entities:
        if ent[1] == "PER":
            words = ent[0].split()
            if len(words) >= 2:  # Берем только фамилию и имя
                name_parts.append(" ".join(words[:2]))

    # Если spaCy не нашел сущности, пробуем регулярные выражения
    if not name_parts:
        # Регулярное выражение для поиска имени и фамилии (в любом порядке)
        full_name_pattern = r"\b([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)(?:\s+[А-ЯЁ][а-яё]+)?\b"
        match = re.search(full_name_pattern, personal_block)
        if match:
            first_name = match.group(1)
            last_name = match.group(2)
            return {"name": f"{first_name} {last_name}"}

    # Если найдены сущности через spaCy, берем первые две части
    if len(name_parts) >= 1:
        return {"name": name_parts[0]}  # Берем первое найденное имя

    return {"name": ""}
#----------------------------------SKILLS

SKILLS_KEYWORDS = [
"sql", "java", "api", "python","R","javascript", "html", "css", "react", "angular", "vue.js", "postgresql", "mysql", "mongodb", "машинное обучение", "глубокое обучение", "pandas", "numpy", "matplotlib", "hadoop", "spark", "aws", "azure", "google cloud", "docker", "kubernetes", "jenkins", "gitlab ci", "git", "devops", "unit testing", "selenium", "rest", "graphql", "linux", "микросервисы", "tensorflow", "pytorch", "алгоритмы", "структуры данных", "nosql", "apache airflow", "talend", "flutter", "swift", "kotlin", "c++", "c#", ".net", "php", "ruby", "bash", "powershell", "terraform", "ansible", "prometheus", "grafana", "kafka", "rabbitmq", "opencv", "computer vision", "natural language processing", "blockchain", "solidity", "rust", "go", "firebase", "elasticsearch", "kibana", "java", "python", "ruby", "php", "node.js", "c#", "go", "rust", "scala", "elixir", "spring", "django", "flask", "express.js", "ruby on rails", "asp.net core", "laravel", "oracle", "mariadb", "sqlite", "redis", "cassandra", "couchbase", "neo4j", "arangodb", "memcached", "varnish", "hazelcast", "rabbitmq", "apache kafka", "activemq", "zeromq", "nats", "event-driven architecture", "cqrs", "ddd", "hexagonal architecture", "grpc", "soap", "openapi", "swagger", "fastapi", "svelte", "ember.js", "backbone.js", "next.js", "nuxt.js", "gatsby", "tailwind css", "bootstrap", "foundation", "bulma", "materialize", "sass", "scss", "less", "stylus", "webpack", "vite", "rollup", "parcel", "babel", "d3.js", "three.js", "chart.js", "pixijs", "redux", "vuex", "zustand", "mobx", "recoil", "jest", "mocha", "chai", "cypress", "playwright", "storybook", "meteor.js", "nestjs", "adonisjs", "fastify", "yeoman", "hygen", "sentry", "logrocket", "datadog", "podman", "lxc", "lxd", "buildah", "nomad", "rancher", "circleci", "travis ci", "bitbucket pipelines", "spinnaker", "pulumi", "cloudformation", "cdk", "crossplane", "elk stack", "loki", "splunk", "new relic", "istio", "envoy", "traefik", "haproxy", "vault", "keycloak", "open policy agent", "scikit-learn", "xgboost", "lightgbm", "catboost", "statsmodels", "jax", "mxnet", "hugging face transformers", "fastai", "nltk", "spacy", "gensim", "textblob", "pil", "pillow", "albumentations", "detectron2", "flink", "hive", "impala", "presto", "drill", "seaborn", "plotly", "bokeh", "altair", "dash", "mlflow", "kubeflow", "tfx", "metaflow", "jetpack compose", "room", "retrofit", "dagger", "hilt", "swiftui", "combine", "coredata", "alamofire", "react native", "xamarin", "ionic", "capacitor", "appium", "espresso", "xctest", "unity", "unreal engine", "godot", "cryengine", "lumberyard", "c++", "c#", "lua", "gdscript", "physx", "bullet physics", "opengl", "directx", "vulkan", "photon", "mirror", "nakama", "blender", "maya", "3ds max", "houdini", "ethereum", "solana", "polkadot", "cardano", "avalanche", "polygon", "vyper", "clarity", "move", "truffle", "hardhat", "brownie", "foundry", "libsodium", "openssl", "bouncy castle", "uniswap sdk", "aave protocol", "compound finance", "erc-721", "erc-1155", "ipfs", "pinata", "burp suite", "owasp zap", "nikto", "nessus", "metasploit", "nmap", "wireshark", "hydra", "owasp dependency-check", "sonarqube", "qradar", "arcsight", "sentinelone", "thehive", "cortex", "misp", "lambda", "s3", "ec2", "rds", "dynamodb", "cloudfront", "ecs", "eks", "azure functions", "blob storage", "aks", "cosmos db", "logic apps", "cloud functions", "bigquery", "pub/sub", "kubernetes engine", "serverless framework", "aws sam", "google cloud run", "aws migration hub", "azure migrate", "google transfer appliance", "c", "assembly", "micropython", "lua", "freertos", "zephyr", "vxworks", "arduino", "raspberry pi", "esp32", "stm32", "mqtt", "coap", "zigbee", "lorawan", "modbus", "keil", "iar embedded workbench", "platformio", "testng", "cucumber", "gauge", "karate", "jmeter", "gatling", "locust", "owasp dependency-check", "snyk", "fortify", "detox", "earlgrey", "xctest", "bdd", "tdd"
]

# Создание PhraseMatcher
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")  # Поиск без учета регистра

# Добавление навыков в matcher
patterns = [nlp(skill) for skill in SKILLS_KEYWORDS]
matcher.add("SKILLS", patterns)

def process_skills(text: str) -> list:

    doc = nlp(text)
    matches = matcher(doc)
    skills_found = set()

    for match_id, start, end in matches:
        skill = doc[start:end].text  # Извлечение текста совпадения
        skills_found.add(skill.lower())  # Приведение к нижнему регистру для избежания дубликатов

    return list(skills_found)


#-----------------------------------УРОВЕНЬ АНГЛИЙСКОГО
ENGLISH_LEVELS = {
    "начальный": "A1",
    "ниже среднего": "A2",
    "средний": "B1",
    "выше среднего": "B2",
    "продвинутый": "C1",
    "владение в совершенстве": "C2",
    "beginner": "A1",
    "elementary": "A2",
    "pre-intermediate": "A2",
    "intermediate": "B1",
    "upper-intermediate": "B2",
    "advanced": "C1",
    "proficiency": "C2"
}

def extract_english_level(text: str) -> str:
    # Приводим текст к нижнему регистру для удобства поиска
    cleaned_text = text.lower()

    # Ключевые слова, указывающие на контекст английского языка
    context_keywords = [
        "английский", "english", "английского"
    ]

    # Шаблоны для поиска уровня в контексте
    for level, cefr in ENGLISH_LEVELS.items():
        # Создаем шаблон для поиска уровня рядом с ключевыми словами
        pattern = rf"(?:{'|'.join(context_keywords)})\s*[:\-]?\s*({re.escape(level)})"
        match = re.search(pattern, cleaned_text)
        if match:
            return cefr  # Возвращаем соответствующий уровень CEFR

    # Если уровень не найден в контексте, проверяем стандартные обозначения A1-C2
    cefr_pattern = r"\b(?:A1|A2|B1|B2|C1|C2)\b"
    cefr_match = re.search(cefr_pattern, text, re.IGNORECASE)
    if cefr_match:
        return cefr_match.group(0).upper()

    # Если ничего не найдено, возвращаем пустую строку
    return "-"

#--------------------------------ОБРАЗОВАНИЕ И РЕЙТИНГ

def normalize_name(name: str) -> str:
    """
    Нормализация названия для сравнения.
    """
    # Приводим к нижнему регистру
    name = name.lower()
    # Удаляем лишние символы (запятые, скобки)
    name = re.sub(r"[,\(\)]", "", name)
    # Удаляем слова, которые могут мешать сравнению
    # name = re.sub(r"\bгосударственный университет\b", "", name)
    # Убираем лишние пробелы
    return name.strip()

def compare_word_sets(name1: str, name2: str, threshold: float = 0.7) -> bool:
    """
    Сравнивает два названия как множества слов.
    Возвращает True, если степень совпадения выше порога.
    """
    set1 = set(normalize_name(name1).split())
    set2 = set(normalize_name(name2).split())

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    similarity = intersection / union if union > 0 else 0
    print(similarity)
    return similarity >= threshold
list_uni = []

# def search_university_position(university_name: str) -> str:
#     """
#     Поиск позиции университета через AJAX-запрос на сайте.
#     """
#     url = "https://russiaedu.ru/_ajax/rating"
#     headers = {
#         "Accept": "application/json, text/javascript, */*; q=0.01",
#         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
#         "Referer": "https://russiaedu.ru/rating",
#         "X-Requested-With": "XMLHttpRequest"
#     }
#     data = {
#         "edu_university[searchString]": university_name,  # Параметр для поиска
#         "pp": "10",  # Количество результатов на страницу
#         "pageNumber": "1"  # Номер страницы
#     }
#
#     try:
#         response = requests.post(url, headers=headers, data=data)
#         response.raise_for_status()
#
#         # Парсинг JSON-ответа
#         json_data = response.json()
#         print("J :  ", json_data)
#
#         if "rating" in json_data:
#             # Нормализуем название из запроса
#             normalized_university_name = normalize_name(university_name)
#             print('from query: ',normalized_university_name)
#             for result in json_data["rating"]:
#                 org = result.get("org", {})
#                 name = org.get("name", "").strip()
#                 position = result.get("position", "")
#
#                 # Нормализуем название из JSON
#                 normalized_name = normalize_name(name)
#                 print("from json :",normalized_name)
#                 # Сравниваем названия как множества слов
#                 if compare_word_sets(university_name, name):
#                     return position
#
#         logging.warning(f"Позиция для университета '{university_name}' не найдена на сайте.")
#         return "-"
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Ошибка при запросе позиции для университета '{university_name}': {e}")
#         return "-"
#
#     except Exception as e:
#         logging.error(f"Неизвестная ошибка при поиске позиции для университета '{university_name}': {e}")
#         return "-"





def load_universities(file_path: str) -> Dict[str, str]:
    """
    Загружает названия университетов из файла uni.txt.
    Возвращает словарь, где ключ — аббревиатура, значение — полное название.
    """
    universities = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Убираем кавычки и разделяем по запятой
                parts = [part.strip('"').strip() for part in line.strip().split(",")]
                if len(parts) == 2:
                    abbreviation, full_name = parts
                    universities[abbreviation.lower()] = full_name.lower()
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
    return universities

# def process_education(education_block: str, universities: Dict[str, str]) -> Dict[str, str]:
#     """
#     Извлечение данных об образовании и специальности.
#     """
#     data = {
#         "university": None,
#         "specialization": None,
#         "rating": None
#     }
#
#     # Списки синонимов для поиска
#     university_keywords = [
#         "университет", "институт", "академия", "колледж", "школа", "вуз",
#         "технический университет", "государственный университет",
#         "исследовательский университет", "политехнический университет",
#         "ядерный университет", "национальный исследовательский"
#     ]
#     specialization_keywords = [
#         "специальность", "профиль", "направление", "квалификация", "дисциплина"
#     ]
#
#     # Приводим текст к нижнему регистру
#     education_block = education_block.lower()
#     # Проверяем, начинается ли блок с ключевого слова "образование"
#     if  education_block.startswith("образование"):
#         # return data  # Если ключевого слова нет, возвращаем пустые данные
#
#         # Нормализуем текст
#         normalized_block = normalize_name(education_block)
#         print("Norm :",normalized_block)
#         # Поиск университета
#         for keyword in university_keywords:
#             if keyword in normalized_block:
#                 # Ищем подстроку, содержащую название университета
#                 match = re.search(rf"\b{keyword}\b.*?([^\n]+)", normalized_block)
#                 if match:
#                     university_candidate = match.group(1).strip()
#                     # Проверяем, есть ли найденный университет в списке
#                     for abbreviation, full_name in universities.items():
#                         if (normalize_name(abbreviation) in normalize_name(university_candidate) or
#                                 normalize_name(full_name) in normalize_name(university_candidate)):
#                             print("uni:",data["university"])
#                             data["university"] = full_name
#                             data["rating"] = search_university_position(abbreviation)
#                             break
#                     if data["university"]:
#                         print("uni:_f", data["university"])
#                         break
#
#     # Если университет не найден
#     if not data["university"]:
#         data["university"] = "-"
#         data["rating"] = "-"
#
#     # Поиск специальности
#     for keyword in specialization_keywords:
#         if keyword in normalized_block:
#             match = re.search(rf"\b{keyword}\b.*?([^\n]+)", normalized_block)
#             if match:
#                 data["specialization"] = match.group(1).strip()
#                 break
#
#     return data

#=====================================РАНЖИРОВАНИЕ======================================
#
# <<<<<<< HEAD
# =======
#     # Приводим текст к нижнему регистру
#     education_block = education_block.lower()
#     # Проверяем, начинается ли блок с ключевого слова "образование"
#     if  education_block.startswith("образование"):
#         # return data  # Если ключевого слова нет, возвращаем пустые данные
#
#         # Нормализуем текст
#         normalized_block = normalize_name(education_block)
#         print("Norm :",normalized_block)
#         # Поиск университета
#         for keyword in university_keywords:
#             if keyword in normalized_block:
#                 # Ищем подстроку, содержащую название университета
#                 match = re.search(rf"\b{keyword}\b.*?([^\n]+)", normalized_block)
#                 if match:
#                     university_candidate = match.group(1).strip()
#                     # Проверяем, есть ли найденный университет в списке
#                     for abbreviation, full_name in universities.items():
#                         if (normalize_name(abbreviation) in normalize_name(university_candidate) or
#                                 normalize_name(full_name) in normalize_name(university_candidate)):
#                             print("uni:",data["university"])
#                             data["university"] = full_name
#                             data["rating"] = search_university_position(abbreviation)
#                             break
#                     if data["university"]:
#                         print("uni:_f", data["university"])
#                         break
#
#     # Если университет не найден
#     if not data["university"]:
#         data["university"] = "-"
#         data["rating"] = "-"
#
#     # Поиск специальности
#     for keyword in specialization_keywords:
#         if keyword in normalized_block:
#             match = re.search(rf"\b{keyword}\b.*?([^\n]+)", normalized_block)
#             if match:
#                 data["specialization"] = match.group(1).strip()
#                 break
#
#     return data
# print("colab")
# >>>>>>> origin/feature/text_processing_resume
