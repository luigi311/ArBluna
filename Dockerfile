# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV LUNA_TO_BLUNA_RATIO=1.05
ENV BLUNA_TO_LUNA_RATIO=0.96
ENV MIN_TRADE_BALANCE=0.01
ENV MIN_UST_BALANCE=3
ENV TARGET_UST_BALANCE=5
ENV SLEEP_DURATION=10
ENV NOTIFY_SLACK=False
ENV NOTIFY_TELEGRAM=False
ENV PUBLIC_NODE_URL=https://lcd.terra.dev
ENV LUNA_UST_PAIR_ADDRESS=terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6
ENV LUNA_BLUNA_PAIR_ADDRESS=terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p
ENV BLUNA_CONTRACT=terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp
ENV MAX_SPREAD=0.01

# Install pip requirements
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python","main.py"]
