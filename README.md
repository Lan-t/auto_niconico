# ニコ動のランキング自動再生するやつ

名前通り  
  

Usage: 
最初だけ `pip install -r requirements.txt`  
`$ python main.py ランキングのURL [-l --loop] [-s --shuffle] [-c --no-comment] [-f --fullscreen] [-a --login] [--user=username] [--password=password]`  

--loginすると最初にログイン画面が開く  
--user, --passwordを両方指定すると自動でログインする(パスワード平文は怖いのでおすすめしない)  
入力しなかったら開いたブラウザに入れてログイン 

一時停止とかは開いたブラウザから直接  
シークバーとかも動かして大丈夫  

ランキング以外でもクエリにrss=2.0ってつけるとxmlが振ってくるタイプのやつならなんでも

終わるときはブラウザ閉じる(コンソールはエラー吐くけど気にしない)  
