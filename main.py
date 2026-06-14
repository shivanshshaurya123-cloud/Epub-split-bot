import os
import logging
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
from openai import OpenAI

===== ENV VARIABLES =====

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

===== API CLIENT =====

client = OpenAI(
base_url="https://router.huggingface.co/v1",
api_key=HF_TOKEN,
)

logging.basicConfig(level=logging.INFO)

===== FLASK =====

app = Flask(name)

===== USER SETTINGS =====

user_parts = {}

===== EPUB READ =====

def extract_epub(file_path):
book = epub.read_epub(file_path)
chapters = []

for item in book.get_items():
    if item.get_type() == 9:
        soup = BeautifulSoup(item.get_body_content(), "html.parser")
        text = soup.get_text()
        if text.strip():
            chapters.append(text)

return chapters

===== SPLIT =====

def split_data(chapters, parts):
size = max(1, len(chapters) // parts)
result = []

for i in range(0, len(chapters), size):
    result.append("\n\n".join(chapters[i:i+size]))

return result

===== TRANSLATE =====

def translate(text):
try:
res = client.chat.completions.create(
model="deepseek-ai/DeepSeek-V4-Pro:novita",
messages=[{"role": "user", "content": f"Translate into Hindi:\n{text[:4000]}"}],
)
return res.choices[0].message.content
except:
return text

===== FILE CREATE =====

def create_files(text, name):
txt = f"{name}.txt"
doc = f"{name}.docx"

with open(txt, "w", encoding="utf-8") as f:
    f.write(text)

d = Document()
d.add_paragraph(text)
d.save(doc)

return txt, doc

===== COMMANDS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"Send EPUB file\nUse /set 10 to split into parts"
)

async def set_parts(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
parts = int(context.args[0])
user_parts[update.effective_user.id] = parts
await update.message.reply_text(f"Parts set to {parts}")
except:
await update.message.reply_text("Usage: /set 10")

===== HANDLE FILE =====

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
file = await update.message.document.get_file()
await file.download_to_drive("book.epub")

await update.message.reply_text("Processing...")

chapters = extract_epub("book.epub")
parts = user_parts.get(update.effective_user.id, 5)

split = split_data(chapters, parts)

for i, part in enumerate(split, 1):
    translated = translate(part)

    txt, doc = create_files(translated, f"part_{i}")

    await update.message.reply_document(InputFile(txt))
    await update.message.reply_document(InputFile(doc))

await update.message.reply_text("Done")

===== MAIN =====

def run_bot():
app_tg = Application.builder().token(BOT_TOKEN).build()

app_tg.add_handler(CommandHandler("start", start))
app_tg.add_handler(CommandHandler("set", set_parts))
app_tg.add_handler(MessageHandler(filters.Document.ALL, handle_file))

app_tg.run_polling()

===== WEB FOR RENDER =====

@app.route("/")
def home():
return "Bot running"

if name == "main":
run_bot()
