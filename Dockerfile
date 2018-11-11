FROM gorialis/discord.py:alpine-rewrite-full

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./kiara.py" ]