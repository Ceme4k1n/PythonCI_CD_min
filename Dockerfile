FROM python:3.9-slim

# Настройка прокси
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание необходимых директорий
RUN mkdir -p /projects /app/database

# Установка прав доступа
RUN chmod 777 /projects /app/database

# Копирование файлов проекта
COPY . .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание группы docker и добавление пользователя
RUN groupadd -r docker && \
    useradd -r -g docker botuser && \
    usermod -aG docker botuser && \
    chown -R botuser:docker /app /projects

# Установка прав на Docker socket
RUN touch /var/run/docker.sock && \
    chmod 666 /var/run/docker.sock

# Переключение на пользователя
USER botuser

# Запуск бота
CMD ["python", "main.py"] 