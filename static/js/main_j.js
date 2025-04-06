// Общие элементы
const fileInput = document.getElementById('resume-upload');
const uploadedFilesList = document.getElementById('uploaded-files-list');
const progressBar = document.getElementById('progress-bar');
const filterForm = document.getElementById('filter-form');
const experienceInput = document.getElementById('experience');

// Проверка существования элементов
if (!fileInput || !uploadedFilesList || !progressBar || !filterForm) {
    console.error('Необходимые элементы не найдены в DOM.');
}

// Обработчик загрузки файлов
fileInput?.addEventListener('change', (event) => {
    const files = event.target.files;
    if (files.length === 0) return;

    // Проверка расширений файлов
    const allowedExtensions = /(\.pdf)$/i;
    let hasInvalidFile = false;
    for (const file of files) {
        if (!allowedExtensions.exec(file.name)) {
            alert(`Файл "${file.name}" не является PDF.`);
            hasInvalidFile = true;
            fileInput.value = '';
            break;
        }
    }

    if (hasInvalidFile) return;

    // Отображение выбранных файлов
    uploadedFilesList.innerHTML = '';
    for (const file of files) {
        const listItem = document.createElement('li');
        listItem.textContent = `⮹ ${file.name}`;
        uploadedFilesList.appendChild(listItem);
    }

    // Настройка FormData
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }

    // Настройка XMLHttpRequest
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);

    // Прогресс загрузки
    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total * 100).toFixed(0);
            progressBar.style.width = `${percent}%`;
            progressBar.textContent = `${percent}%`;
        }
    };

    // Обработка ответа
    xhr.onload = () => {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            progressBar.style.backgroundColor = '#4CAF50';

            // Отображение результатов
            response.results.forEach(result => {
                const listItem = document.createElement('li');
                listItem.textContent = `${result.filename}: ${result.message}`;
                listItem.style.color = result.status === 'success' ? 'green' : 'red';
                uploadedFilesList.appendChild(listItem);
            });

            setTimeout(() => {
                progressBar.style.width = '0%';
                progressBar.textContent = '';
                progressBar.style.backgroundColor = '#007bff';
                alert('Загрузка завершена!');
            }, 2000);
        } else {
            progressBar.style.backgroundColor = '#ff0000';
            alert('Ошибка загрузки!');
        }
    };

    xhr.send(formData);
});

// Инициализация страницы рейтинга
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const position = urlParams.get('position');

    if (position) {
        document.getElementById('position-title').textContent = position || 'Не указана';
        // Здесь будет запрос к API для получения данных кандидатов
    }
});

// Восстановление состояния чекбоксов и обновление интерфейса
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.dropdown-content input').forEach(checkbox => {
        const key = `cb_${checkbox.name}_${checkbox.value}`;
        checkbox.checked = localStorage.getItem(key) === 'true';
    });
    updateSelectedDisplays();
});

document.querySelectorAll('.dropdown-content input').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
        const key = `cb_${checkbox.name}_${checkbox.value}`;
        localStorage.setItem(key, e.target.checked);
        updateSelectedDisplays();
    });
});

function updateSelectedDisplays() {
    document.querySelectorAll('.custom-dropdown').forEach(container => {
        const selected = Array.from(container.querySelectorAll('input:checked'))
            .map(el => el.parentElement.textContent.trim())
            .join(', ');

        const button = container.querySelector('.dropbtn');
        const defaultText = button.getAttribute('data-default-text');

        // Обновление текста кнопки
        button.textContent = selected
            ? selected
            : defaultText || 'Выберите...';
    });
}

// Обработчики выпадающих списков
document.querySelectorAll('.dropbtn').forEach(btn => {
    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const menu = this.parentElement.querySelector('.dropdown-content');
        menu.classList.toggle('show');
    });
});

// Закрытие выпадающих списков при клике вне
document.addEventListener('click', (e) => {
    document.querySelectorAll('.dropdown-content').forEach(menu => {
        if (!menu.contains(e.target) && !menu.previousElementSibling.contains(e.target)) {
            menu.classList.remove('show');
        }
    });
});

// Валидация ручного ввода для опыта работы
document.getElementById('experience').addEventListener('input', (e) => {
    let value = parseInt(e.target.value) || 0;
    value = Math.max(0, Math.min(50, value));
    e.target.value = value;
});

// Обработчик формы фильтров
filterForm?.addEventListener('submit', (event) => {
    event.preventDefault();

    // Сбор данных из кастомных списков
    const getChecked = (name) => {
        return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
            .map(checkbox => checkbox.value);
    };

    const filters = {
        position: document.getElementById('position')?.value || '',
        employment_type: document.getElementById('employment_type')?.value || '',
        competency_level: document.getElementById('competency_level')?.value || '',
        work_format: getChecked('work_format'),
        education: getChecked('education'),
        experience: document.getElementById('experience')?.value || '0',
        skills: getChecked('skills'),
        english_level: getChecked('english_level'),
        special_requirements: document.getElementById('special_requirements')?.value || ''
    };

    console.log('Фильтры:', filters);
    // Здесь добавьте отправку на сервер
});

// Сброс формы
document.getElementById('reset-filters')?.addEventListener('click', () => {
    // Сброс чекбоксов
    document.querySelectorAll('.dropdown-content input').forEach(input => {
        input.checked = false;
    });

    // Очистка localStorage
    localStorage.clear();

    // Сброс текстовых полей и селектов
    document.querySelectorAll('.form-group input, .form-group select').forEach(input => {
        if (input.type !== 'checkbox' && input.type !== 'file') {
            input.value = '';
        }
    });

    // Сброс текста кнопок
    document.querySelectorAll('.dropbtn').forEach(btn => {
        btn.textContent = 'Выберите';
    });

    // Сброс счетчика опыта работы
    experienceInput.value = '0';

    // Очистка контейнеров с выбранными значениями
    document.querySelectorAll('.selected-display').forEach(display => {
        display.textContent = '';
    });
});

// Обработчик кнопки показа рейтинга
document.getElementById('show-ranking')?.addEventListener('click', () => {
    const position = document.getElementById('position').value;
    window.location.href = `/ranking?position=${encodeURIComponent(position)}`;
});