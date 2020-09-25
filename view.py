import os
from flask import Flask, render_template, request, redirect, url_for, flash
# from werkzeug import secure_filename
from werkzeug.utils import secure_filename
import datetime
import tweepy
import ast
import requests
import json
import copy

#### 必要な情報を整理しやすいよう外部ファイル化####
import info_val

Consumer_key = info_val.Consumer_key
Consumer_secret = info_val.Consumer_secret
Access_token = info_val.Access_token
Access_secret = info_val.Access_secret
text_analytics_base_url =info_val.text_analytics_base_url
sentiment_api_url =  info_val.sentiment_api_url
subscription_key = info_val.subscription_key

# appという名前でFlaskオブジェクトをインスタンス化
app = Flask(__name__)

# rootディレクトリにアクセスした場合の挙動
@app.route('/')
def index():
        return render_template('index.html')

# 分析ボタン押下時の挙動
@app.route('/analytics', methods=['GET', 'POST'])

def analytics_positive():
    app.logger.debug(type(request.form.to_dict(flat=False) ))
    res = request.form.to_dict(flat=False)
    twitter_id = res['twitter_id'][0]
    app.logger.debug(twitter_id)
    if request.method == 'POST':
        # OAuth認証
        auth = tweepy.OAuthHandler(Consumer_key, Consumer_secret)
        auth.set_access_token(Access_token, Access_secret)
        api = tweepy.API(auth)

        azure_json = ""
        results = api.user_timeline(screen_name=twitter_id, count=200, page=1)
        for num, result in enumerate(results):
            azure_json_single = str({'id': num,\
                             'language':'ja',\
                             'text':result.text\
                            })
            azure_json += azure_json_single + ','
        #最後だけカンマ抜く
        azure_json=azure_json[:-1]
        azure_json = "{'documents' : ["+ azure_json+"]}"
        azure_json = ast.literal_eval(azure_json)

        #request 処理
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        response = requests.post(sentiment_api_url, headers=headers, json=azure_json)
        sentiments = response.json()

        total = 0
        count = 0
        for score in sentiments['documents']:
            total += score['detectedLanguage']['confidenceScore']
            count = count + 1 

        score = (total/count - 0.8) * 5

        return render_template(
                    'analytics.html',
                    score = score
                )
    else:
        return render_template('index.html')

# メインで実行される関数
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)