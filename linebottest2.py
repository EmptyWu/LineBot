#from flask_ngrok import run_with_ngrok
from flask import Flask, request
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os,json

from openai import OpenAI
client = OpenAI(
    api_key = os.environ.get("OpenAIKey","None")     # 你的 OpenAI API KEY
)

from firebase import firebase
url = os.environ.get("firebaseurl","None")    # 你的 Firebase Realtime database URL
fdb = firebase.FirebaseApplication(url, None)

secret=os.environ.get("secret","None")    # 你的 Channel Secret
configuration = Configuration(access_token=os.environ.get("accesstoken","None"))    # 你的 Access Token
handler = WebhookHandler(secret)

app = Flask(__name__)



@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    print(json_data)
    try:
      

        signature = request.headers['X-Line-Signature']
        linebot_api = MessagingApi(ApiClient(configuration))

        # get request body as text
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)
        json_data = json.loads(body)
        
        tk = json_data['events'][0]['replyToken']            # 回覆的 reply token
        timestamp = json_data['events'][0]['timestamp']      # 訊息時間戳
        msg_type = json_data['events'][0]['message']['type'] # 訊息類型
        chatgpt = fdb.get('/','chatgpt')                 # 讀取 Firebase 資料庫內容

        # 如果是文字訊息
        if msg_type == 'text':
            msg = json_data['events'][0]['message']['text']  # 取出文字內容
            print(msg)

            if chatgpt == None:
                messages = []       # 如果資料庫裡沒有內容，建立空串列
            else:
                messages = chatgpt  # 如果資料庫裡有內容，設定歷史紀錄為資料庫內容
            print(chatgpt)

            #判斷msg在messages裡有值
            exists = check_existence(messages, msg)
            if exists:
                return 'OK'

            if msg == '!reset' or msg=='清除所有歷史紀錄':
                fdb.delete('/','chatgpt')    # 如果收到 !reset 的訊息，表示清空資料庫內容
                #db.collection(u'/').document(u'chat').delete()
                ai_msg = TextMessage(text='對話歷史紀錄已經清空！')
            else:
                messages.append({"role":"user","content":msg})  # 如果是一般文字訊息，將訊息添加到歷史紀錄裡
                response = client.chat.completions.create(
                    model="text-embedding-3-small",
                    max_tokens=128,
                    temperature=0.5,
                    messages=messages
                )
                print(response)
                ai_msg = response.choices[0].message.content.replace('\n','')  # 移除回應裡的換行符
                messages.append({"role":"assistant","content":ai_msg})  # 歷史紀錄裡添加回應訊息
                fdb.put('/','chatgpt',messages)        # 使用非同步的方式紀錄訊息
                print(ai_msg)
              
            linebot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=tk,
                        messages=[TextMessage(text=ai_msg)]
                    )
                )
        else:
            reply_msg = TextMessage(text='你傳的不是文字訊息呦')
            linebot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=tk,
                        messages=[TextMessage(text=reply_msg)]
                    )
                )
    except:
        print('error')
    return 'OK'

def check_existence(data, target):
    for item in data:
        if item['content'] == target and item['role'] == 'user':
            return True
    return False

if __name__ == "__main__":
  from gevent import pywsgi
  server = pywsgi.WSGIServer(('0.0.0.0',5000),app)
  server.serve_forever()
  app.run()