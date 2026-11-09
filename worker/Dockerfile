FROM python:3.11-slim
WORKDIR /app
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY worker/label_worker.py worker/storage.py worker/clean.py /app/
COPY prompts/teacher_prompt.txt /app/prompts/teacher_prompt.txt
COPY data/schema.json /app/data/schema.json
ENV PROMPT_PATH=/app/prompts/teacher_prompt.txt
CMD ["python", "label_worker.py"]
