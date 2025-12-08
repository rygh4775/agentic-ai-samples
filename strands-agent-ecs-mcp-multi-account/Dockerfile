FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ecs_agent.py .

EXPOSE 8080

CMD ["python", "ecs_agent.py"]
