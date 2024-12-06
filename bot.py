import os
from flask import Flask, request
import requests
from PyPDF2 import PdfReader
from googletrans import Translator

# إعداد التطبيق Flask
app = Flask(__name__)

# تعريف التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN")

# عنوان API الخاص بتليغرام
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# مترجم Google
translator = Translator()

# نقطة البداية
@app.route("/")
def index():
    return "Bot is running!"

# استلام رسائل Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    
    # التحقق من وجود ملف
    if "message" in data and "document" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        file_id = data["message"]["document"]["file_id"]
        
        # تنزيل الملف
        file_info = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        file_content = requests.get(file_url).content
        
        # حفظ الملف مؤقتًا
        with open("uploaded.pdf", "wb") as pdf_file:
            pdf_file.write(file_content)
        
        # قراءة وترجمة محتوى PDF
        try:
            reader = PdfReader("uploaded.pdf")
            translated_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    translated_text += translator.translate(text, src="auto", dest="ar").text + "\n"
            
            # إرسال النص المترجم
            send_message(chat_id, translated_text[:4096])  # تقييد النص بـ 4096 حرفًا
        except Exception as e:
            send_message(chat_id, "حدث خطأ أثناء قراءة الملف أو ترجمته.")
        
        # حذف الملف المؤقت
        os.remove("uploaded.pdf")
    else:
        # الرد إذا لم يكن هناك ملف
        chat_id = data["message"]["chat"]["id"]
        send_message(chat_id, "يرجى إرسال ملف PDF لترجمته.")
    
    return "OK"

# وظيفة إرسال الرسائل
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
