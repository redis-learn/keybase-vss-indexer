FROM docker.io/python:3.9
WORKDIR ./
COPY . /

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "reader.py" ]