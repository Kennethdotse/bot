# standard_speech_bot_vercel.py
import logging
import random
import json
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Voice, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from fastapi import FastAPI, Request
import uvicorn

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Load Token ---
load_dotenv()
BOT_TOKEN = os.getenv("STANDARD_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing STANDARD_BOT_TOKEN in .env")

# --- Storage folders ---
os.makedirs("audio", exist_ok=True)
os.makedirs("metadata", exist_ok=True)

# --- Constants ---
STANDARD_MAX_PROMPTS = 5

# --- State dictionaries ---
user_has_consented = {}
user_metadata = {}
user_prompts = {}
user_prompt_index = {}
user_temp_voice = {}

# --- Prompts ---
STANDARD_CODE_SWITCHED_PROMPTS = [
    "Mepɛ sɛ me kɔ town later",
    "Hwɛ, I told you not to do that.",
    "Wobɛ ba anɔpa? Let me know early.",
    "He's not nice at all, me bo afu.",
    "Mabrɛ oo, today’s work was too much.",
    "Ɛnyɛ easy o, but we move.",
    "Kɔtɔ no wɔ hɔ? I want to buy some.",
    "Ne ho yɛ me fɛ, I like him.",
    "Wo pɛ dɛn? Tell me what you want.",
    "I’m hungry paa, yɛnkɔ didi.",
    "M’ani agye paao, congratulations!.",
    "I’m coming ankasa, give me 5 minutes.",
    "Wo nim sɛ I almost forgot to buy the food?",
    "Me nsa aka, I’m tired.",
    "Ɛyɛ fɛ, I really like this.",
    "Me kɔ aba, wait for me here.",
    "Ɛhe na wokɔ? When will you even come?",
    "Me nte ase, explain again.",
    "Ɛyɛ den oo, but I’ll try.",
    "Wobɛyɛ late o, hurry up.",
    "My entire body yɛ me ya paa.",
    "Ɛyɛ me sɛ he's back.",
    "Mepɛ nanso I’m shy small.",
    "Ɛyɛ okay, don’t worry.",
    "Ɛyɛ me nwanwa, I didn’t expect this.",
    "Mmonka mo ho, we are running late.",
    "Menni sika, can you lend me 50 cedis?",
    "Ɛyɛ a na woafrɛ me, I will be waiting.",
    "Wose sɛn? I didn't hear what you said.",
    "Chale, I am leaving, yɛbɛhyia.",
    "M’ani kum, I need to sleep early today.",
    "Woadi lunch? Let's go and eat.",
    "Hwɛ yie, that place is dangerous.",
    "Mepɛ sɛ me kɔ, are you ready to leave?",
    "Ɛnkyɛ koraa, I will be done in 5 minutes.",

    "Ka kyerɛ no sɛ, the meeting has been moved.",
    "Gyae dede no, I am trying to focus.",
    "Fa to hɔ, yeah.",
    "Kɔ fa bra, I need it right now.",
    "Boa me, this code is not working.",
    "Mabrɛ, I need a vacation urgently.",
    "W’ani agye? That’s nice.",

    "Nsuo ɛtɔ, help me bring the things inside.",
    "Network no yɛ slow, I can't send the file.",
    "Car no wɔ hen? I have been standing here long.",
    "Ɛnyɛ easy o, the traffic was terrible.",
    "Woama me kɔn adɔ, now I want fufu.",
    "Bra ha, come and look at this error.",
    "Sɛ wopɛ a, you can join us later.",
    "Mempɛ saa, please change it for me.",

    "Mepakyew, pass me the book.",
    "Meeba sesiaa, we will discuss bebiaa.",
    "He is tired nti he will rest kakraa.",
    "ɛkom di me, let's eat jollof rice.",
    "Yɛnkɔ shopping for clothes later.",
    "I will call you akyire wai.",
    "She is coming o, sɛ wo bɛba.",

    "Wofiri henfa? I have been looking for you.",
    "Mente aseɛ, can you explain that again?",
    "Ɛyɛ dɛ papa, where did you buy it?",
    "Yɛbɛhyia okyena, around 2 PM.",
    "Mma wo werɛ mfi, everything will be fine.",
    "Watɔ aduane no? I am starving here.",
    "Chale, the traffic is too much, but meeba",
    "Wo ho te sɛn? Hope everything is cool.",
    "Fa bra and bring the laptop along.",
    "Adɛn nti na woyɛ dede like that?",
    "Meekɔ fie, see you later.",
    "Sɛ wowie a, call me immediately.",
    "Obiara nni hɔ o. The place is empty.",
    "Mepa wo kyew, give me some water.",
    "Ɛnyɛ hwee, don't worry about it.",
    "Wopɛ sɛ yɛkɔ cinema anaa? I heard there is a new movie.",
    "Mekɔ bank akɔ withdraw sika.",

    "Sende me MoMo, I need it now.",
    "Wanya alert no? I sent it five minutes ago.",
    "Menni cash, can I pay with my phone?",
    "Meetwɛn sika no, my money is finished.",
    "Sika no sua, please add 20 cedis.",
    "Wobɛtumi asende me airtime? Me credit asa.",
    "Gye wo sika, keep the change.",
    "Mepɛ sɛ me withdraw sika, is the network working?",
    "Ɛyɛ too much, reduce the price.",
    "Wɔaka akyerɛ wo sɛ the payment didn't go through?",

    "Si me wɔ junction no so, I will walk from there.",
    "Driver, mepakyew, slow down, kwan no nyɛ.",
    "Ma te but give me my change.",
    "Traffic wei deɛ, we will be late.",
    "Wopɛ Uber anaa? It is faster than trotro.",
    "Kyerɛ me kwan no, I am lost.",
    "Kɔ w’anim kakra, na fa left.",
    "Y’aduru, start parking the car.",
    "Kwan no nyɛ, the road is very bad here.",
    "Wote henfa? Sendi wo location mame.",

    "Me phone awu, do you have a charger?",
    "Mia button no, the red one on the left.",
    "Network no yɛ slow, I can't download the file.",
    "Sɛ wowie a, send me the link via WhatsApp.",
    "Laptop no ayɛ hye dodo, turn it off.",
    "Wobɛtumi a-install saa app no ama me?",
    "Password no yɛ incorrect, try again.",
    "Mente wo voice, your microphone is muted.",
    "Fa picture no to status, everyone will see it.",
    "Checki wo email, I sent the report.",

    "Bɔdeɛ no yɛ sɛn? Give me three fingers.",
    "Mempɛ nneɛma a onions wɔ mu, I really don't like onions.",
    "Adɛn nti na fufuo no yɛ hard saa?",
    "Tɔ nsuo bra, the one in the bottle.",
    "Yɛnkɔ, I know a good place we can eat.",
    "Rice no aben?",
    "Meekɔ market kɔtɔ nneɛma, do you need anything?",
    "Anka mepɛ waakye, but it is finished.",
    "Fa mako kakra gu so, make it spicy.",
    "Wowei a, wash the plates.",

    "Me ti pae me, I need para.",
    "M’ani agye ama wo, congratulations!",
    "Gyae ntorɔ nu, tell me the truth.",
    "Wo ho mfa wo? You look sick.",
    "Mepɛ asɛm no atie, it sounds very interesting.",
    "Mabrɛ dodo, I cannot walk anymore.",
    "Fa kyɛ me, please. It was a mistake.",
    "Ɛyɛ a suro nu, be careful with him.",
    "Wo bo afu? Why are you quiet?",
    "Mepakyew, boa me, it is an emergency.",

    "Yɛbɛhyia ɔkyena anɔpa, don't be late.",
    "Ennɛ yɛ what date? I have lost track.",
    "Maba ha dadaada, where were you?.",
    "Ɛnnɛ anwummerɛ, we have a meeting.",
    "Wobɛkɔ time bɛn? We need to talk before you leave?",
    "Mame me time kakra, I am almost done.",
    "Yɛ startii 2 o'clock, you are late.",
    "Ɛnkyɛ koraa, just give me a moment.",
    "Mekɔ aba seesei ara, wait for me.",
    "Da bɛn na wobɛba? Thursday?"

]

# --- Helpers ---
def user_audio_dir(user_id: int):
    d = os.path.join("audio", str(user_id))
    os.makedirs(d, exist_ok=True)
    return d

def save_master_csv_entry(user_id: int, entry: dict):
    master_csv = os.path.join("metadata", "master.csv")
    exists = os.path.exists(master_csv)

    with open(master_csv, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow([
                "user_id", "timestamp", "consent",
                "age_range", "speech_type",
                "file_name", "prompt"
            ])
        writer.writerow([
            user_id,
            entry["timestamp"],
            entry["consent"],
            entry["age_range"],
            entry["speech_type"],
            entry["file_name"],
            entry["prompt"],
        ])

def save_user_jsonl(user_id: int):
    path = os.path.join("metadata", f"{user_id}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"user_id": user_id, **user_metadata[user_id]}, f, indent=2)
        f.write("\n")

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_has_consented[user_id] = False
    user_metadata[user_id] = {
        "consent": False,
        "age_range": None,
        "speech_type": "standard",
        "recordings": []
    }
    user_prompts[user_id] = []
    user_prompt_index[user_id] = 0
    user_temp_voice[user_id] = None

    consent_text = (
        "📝 *Project Kasa — Consent to Participate*\n\n"
        "This bot records short code-switched speech samples "
        "(e.g., *“Mepɛ sɛ me kɔ town later”*) to improve speech recognition.\n\n"
        "Your participation is voluntary and you may stop at any time.\n\n"
        "You will:\n"
        "1. Give consent and select your age\n"
        "2. Record five short code-switched prompts\n\n"
        "All recordings are anonymous and used only for research.\n\n"
        "Do you agree to participate?"
    )

    buttons = [
        [InlineKeyboardButton("✅ Yes", callback_data="consent_yes"),
         InlineKeyboardButton("❌ No", callback_data="consent_no")]
    ]

    await update.message.reply_text(consent_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def restart_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    prompts = random.sample(
        STANDARD_CODE_SWITCHED_PROMPTS,
        min(len(STANDARD_CODE_SWITCHED_PROMPTS), STANDARD_MAX_PROMPTS)
    )
    user_prompts[user_id] = prompts
    user_prompt_index[user_id] = 0
    await update.message.reply_text("🔄 Starting a new recording session!")
    await send_standard_prompt(update.message, user_id)

async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "We appreciate your time. See you soon for another session☺"
    )

# --- Button Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Handle consent
    if data in ["consent_yes", "consent_no"]:
        if data == "consent_no":
            await query.edit_message_text("Thank you for your time☺.")
            return
        user_has_consented[user_id] = True
        user_metadata[user_id]["consent"] = True
        await query.edit_message_text("Thank you for consenting! 👍")

        age_buttons = [
            InlineKeyboardButton("<18", callback_data="age_<18"),
            InlineKeyboardButton("18-24", callback_data="age_18-24"),
            InlineKeyboardButton("25-34", callback_data="age_25-34"),
            InlineKeyboardButton("35-44", callback_data="age_35-44"),
            InlineKeyboardButton("45+", callback_data="age_45+"),
        ]
        await query.message.reply_text(
            "Please select your age range:",
            reply_markup=InlineKeyboardMarkup([age_buttons])
        )
        return

    if data.startswith("age_"):
        age = data.split("_")[1]
        user_metadata[user_id]["age_range"] = age
        await query.edit_message_text(f"Age selected: {age}")

        prompts = random.sample(
            STANDARD_CODE_SWITCHED_PROMPTS,
            min(len(STANDARD_CODE_SWITCHED_PROMPTS), STANDARD_MAX_PROMPTS)
        )
        user_prompts[user_id] = prompts
        user_prompt_index[user_id] = 0
        await send_standard_prompt(query.message, user_id)
        return

    # Temporary voice handling
    if data.startswith("voice_"):
        action = data.split("_")[1]
        temp_file_info = user_temp_voice.get(user_id)
        if not temp_file_info:
            await query.edit_message_text("⚠️ No pending recording found. Send a new voice note.")
            return
        file_path = temp_file_info["file_path"]
        file_name = temp_file_info["file_name"]
        prompt_text = temp_file_info["prompt"]

        if action == "save":
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "file_name": file_name,
                "prompt": prompt_text,
                "age_range": user_metadata[user_id]["age_range"],
                "speech_type": "standard",
                "consent": True
            }
            user_metadata[user_id]["recordings"].append(entry)
            save_master_csv_entry(user_id, entry)
            save_user_jsonl(user_id)
            user_temp_voice[user_id] = None
            await query.edit_message_text(f"✅ Recording saved: `{file_name}`", parse_mode="Markdown")
            user_prompt_index[user_id] += 1
            await send_standard_prompt(query.message, user_id)

        elif action == "rerecord":
            if os.path.exists(file_path):
                os.remove(file_path)
            user_temp_voice[user_id] = None
            await query.edit_message_text("♻️ Please re-record the prompt now.")

        elif action == "change":
            if os.path.exists(file_path):
                os.remove(file_path)
            user_temp_voice[user_id] = None
            await query.edit_message_text("🔄 Prompt changed. Please record the new prompt now.")
            await send_standard_prompt(query.message, user_id)

    if data.startswith("session_"):
        action = data.split("_")[1]
        if action == "rerecord":
            prompts = random.sample(
                STANDARD_CODE_SWITCHED_PROMPTS,
                min(len(STANDARD_CODE_SWITCHED_PROMPTS), STANDARD_MAX_PROMPTS)
            )
            user_prompts[user_id] = prompts
            user_prompt_index[user_id] = 0
            await send_standard_prompt(query.message, user_id)
        elif action == "end":
            await query.edit_message_text(
                "We appreciate your time. See you soon for another session☺"
            )

# --- Send Standard Prompt ---
async def send_standard_prompt(context_object, user_id: int):
    idx = user_prompt_index[user_id]
    prompts = user_prompts[user_id]

    if idx >= len(prompts):
        buttons = [
            [
                InlineKeyboardButton("🎤 Record Again", callback_data="session_rerecord"),
                InlineKeyboardButton("👋 End Session", callback_data="session_end")
            ]
        ]
        await context_object.reply_text(
            "🎉 You have completed all recordings!\n\n"
            "Would you like to record another set or end the session?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        save_user_jsonl(user_id)
        return

    prompt_text = prompts[idx]
    stars = "⭐" * idx + "☆" * (len(prompts) - idx)
    user_metadata[user_id]["current_prompt"] = prompt_text

    await context_object.reply_text(
        f"🎤 *Prompt {idx+1}/{len(prompts)}*\n\n"
        f"{prompt_text}\n\n"
        f"Progress: {stars}\n"
        f"Send your voice note now.",
        parse_mode="Markdown"
    )

# --- Voice Handler ---
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not user_has_consented.get(user_id, False):
        await update.message.reply_text("Please start with /start and provide consent.")
        return

    voice: Voice = update.message.voice
    if not voice:
        await update.message.reply_text("Please send a real voice note.")
        return

    file = await voice.get_file()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    audio_dir = user_audio_dir(user_id)

    idx = user_prompt_index[user_id]
    prompt_text = user_prompts[user_id][idx]

    file_name = f"{user_id}_std_{idx+1}_{ts}.ogg"
    file_path = os.path.join(audio_dir, file_name)
    await file.download_to_drive(file_path)

    user_temp_voice[user_id] = {
        "file_path": file_path,
        "file_name": file_name,
        "prompt": prompt_text
    }

    buttons = [
        [
            InlineKeyboardButton("💾 Save", callback_data="voice_save"),
            InlineKeyboardButton("♻️ Re-record", callback_data="voice_rerecord"),
            InlineKeyboardButton("🔄 Change Prompt", callback_data="voice_change")
        ]
    ]

    await update.message.reply_text(
        f"🎤 You sent a recording for:\n{prompt_text}\n\nChoose an action:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- FastAPI for Vercel ---
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().bot(bot).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("restart", restart_session))
application.add_handler(CommandHandler("end", end_session))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.VOICE, voice_handler))

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    """Handle incoming updates from Telegram"""
    update = Update.de_json(await request.json(), bot)
    await application.update_queue.put(update)
    return {"ok": True}

@app.get("/")
def index():
    return "Standard Speech Bot is running on Vercel!"

# --- Set webhook on startup ---
async def on_startup():
    webhook_url = os.getenv("WEBHOOK_URL")  # your deployed URL
    await bot.set_webhook(f"{webhook_url}/{BOT_TOKEN}")

@app.on_event("startup")
async def startup_event():
    await on_startup()
