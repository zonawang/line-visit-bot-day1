# 企業參訪小幫手 — Day 1

這是 LINE Messaging API Webhook。私聊可直接提問；群組中只在 `@Bot` 時回答文字訊息。Webhook 先以 Channel secret 驗證簽章，再使用 Channel access token 回覆。

目前使用 `faq.json` 的通用問答，不含任何未確認的活動時間或地點。Day 2 可在此基礎上加入依群組區分的活動資料。

## 已上線的 Day 1

- 官方帳號：`@920ksdcl`（DevRel Zona）；Channel ID：`2010088861`。
- Cloud Run：`https://devrel-visit-bot-3sv3zqjszq-de.a.run.app`。
- Webhook：`https://devrel-visit-bot-3sv3zqjszq-de.a.run.app/webhook`。LINE Developers 的 Verify 已顯示 Success。
- 官方帳號的 Webhook 與「接受邀請加入群組或多人聊天室」均已啟用；歡迎訊息和自動回應訊息維持關閉。
- 已確認 Channel access token 對應 `@920ksdcl`。尚未在真實 LINE 私聊或群組中完成端到端回覆測試。

實際測試時，先將 `@920ksdcl` 加為好友並在私聊傳「功能」。群組測試請將它邀入測試群組，再用 LINE 的提及功能傳送 `@DevRel Zona 功能`。在群組中單純輸入帳號名稱不會觸發回覆；必須選取 LINE 的提及對象。可再問「參訪需要準備什麼？」；時間、地點等尚未設定的資訊會由 Bot 明說未知。

## 本機執行

需要 Python 3.9 以上，無外部套件。設定 `LINE_CHANNEL_SECRET` 和 `LINE_CHANNEL_ACCESS_TOKEN` 後執行 `python app.py`。`GET /ready` 可檢查服務狀態；LINE Webhook 設為公開 HTTPS 服務的 `/webhook`。

## 修改 FAQ

編輯 `faq.json` 中每項的 `keywords` 與 `answer`。匹配依清單順序進行，因此較具體的問題應排在前面。請只加入已確認且可公開給相關群組的資訊。

## 測試

執行 `python -m unittest discover -p 'test_*.py'`。
