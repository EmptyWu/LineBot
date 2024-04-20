FROM python:3.12-alpine

WORKDIR /app

ENV secret="你的 Channel Secret"
ENV accesstoken="你的 Access Token"
ENV OpenAIKey="你的 OpenAI API KEY"
ENV firebaseurl="你的 Firebase Realtime database URL"
ENV geminiapi="你的 Gemini API KEY"

ADD . /app

RUN pip install -r requirements.txt

ADD firebase /usr/local/lib/python3.12/site-packages/firebase  

EXPOSE 5000

CMD ["python", "linebottest2.py"]