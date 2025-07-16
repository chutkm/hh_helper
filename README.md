# Resume Screening Web Application

## Overview

Modern HR departments face increasing pressure to process vast volumes of resumes efficiently. Manual review methods are labor-intensive, subjective, and prone to errors. This project addresses these limitations by providing an intelligent, automated web-based solution for analyzing and ranking resumes based on customizable criteria.

The application significantly reduces HR operational costs (by 40–50%) by automating routine screening tasks. It leverages parallel processing, structured data storage, and machine learning to deliver high performance and adaptability.

## Key Features

- **Resume Parsing**: Uses `PyPDF2` to extract text from PDF resumes, cleans and converts data to structured JSON format.
- **Customizable Criteria**: Recruiters can define search parameters such as job role, skills, experience level, education, and language proficiency.
- **Parallel Processing**: Implements multithreading for simultaneous parsing of multiple files, improving speed and scalability.
- **Candidate Ranking**: Compares extracted resume data with criteria and ranks candidates accordingly.
- **Data Storage**: Uses PostgreSQL for storing structured resume and criteria data with full CRUD support.
- **Interactive UI**: Built with JavaScript and AJAX for dynamic form handling, file upload progress tracking, and responsive design.
- **FastAPI Backend**: High-performance backend using asynchronous request handling and data validation with Pydantic.

## Advanced Capabilities

The system supports integration with advanced NLP and Deep Learning models for semantic analysis and ranking:

- **Named Entity Recognition (NER)**: Uses `spaCy` for extracting names, skills, languages, and contact details.
- **Summarization**: Implements `FRED-T5-Summarizer`, a T5-based model from the RussianNLP community, to condense work experience and education sections into brief summaries.
- **Semantic Matching (Planned)**: Integration of LLMs (Large Language Models) is under development for more nuanced resume-to-job matching.

## System Architecture

The application follows a modular **client-server architecture**:

- **Frontend**: HTML, JavaScript (AJAX), dynamic forms  
- **Backend**: Python (FastAPI), async request handling  
- **Database**: PostgreSQL via `psycopg2`  
- **Resume Processing**: `PyPDF2`, `json`, `Thread` (parallelization)

<!-- Uncomment and replace with actual image path if needed -->
<!-- ![System Diagram](path/to/uml.png)  
*Figure: UML diagram illustrating system component interaction* -->

## Modules

1. **Criteria Input**: A dynamic form interface to input job requirements and skills.
2. **Resume Processing**: PDF parsing and JSON conversion, stored in a relational database.
3. **Candidate Dashboard**: Filterable ranking page displaying top candidates with resume previews.

## Performance

- **92% accuracy** in direct keyword-based matching  
- **Up to 50 concurrent sessions** supported without loss of performance  
- **Structured data format** enables seamless integration of NLP pipelines  

## Future Enhancements

- Full integration of semantic analysis with LLMs for contextual resume understanding  
- Support for additional formats (DOCX, image-to-text via OCR)  
- Analytics dashboards for HR metrics (e.g., skill distribution, location heatmaps)  

## Technologies

- `FastAPI`, `Pydantic`, `spaCy`, `PyPDF2`, `PostgreSQL`, `psycopg2`, `FRED-T5`, `Thread`, `AJAX`, `JavaScript`

## References

1. [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)  
2. [FastAPI Docs](https://fastapi.tiangolo.com/)  
3. [spaCy NER Models](https://spacy.io/models)  
4. [FRED-T5 on Hugging Face](https://huggingface.co/ai-forever/FRED-T5)  
5. [PostgreSQL Documentation](https://www.postgresql.org/docs/)  
6. [RussianNLP Project](https://github.com/sberbank-ai/ru-nlp-models)  

---

