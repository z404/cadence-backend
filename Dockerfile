FROM python:3.8

COPY . .

RUN apt-get update
RUN apt-get install -y python3-pip build-essential curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN pip install -r requirements.txt
RUN python -m snips_nlu download-entity snips/city en

EXPOSE 80

CMD ["-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]
ENTRYPOINT [ "python" ]