import logging
import random
import json
import csv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Voice
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --- Setup Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# --- Ensure folders exist ---
os.makedirs("audio", exist_ok=True)
os.makedirs("metadata", exist_ok=True)

# --- User Data Storage ---
user_metadata = {}      # Stores age, severity, origin, recordings
user_prompts = {}       # Randomized prompts per user
user_prompt_index = {}  # Tracks current prompt index
TOTAL_RECORDINGS = 9

# --- Prompts ---
NORMAL_PROMPTS = [
    "The sun rises in the east and sets in the west.",
    "Please give me the water.",
    "I like to eat mangoes every morning.",
    "My friend plays football at school.",
    "The cat is sitting on the red mat.",
    "I am going to the market to buy yam and rice.",
    "She sings beautifully under the mango tree.",
    "Today is a bright sunny day in Kumasi.",
    "The baby is sleeping."
]

CODE_SWITCHED_PROMPTS = [
    "mepakyew take the book from the table.",
    "I will meet you akyire wai, we go talk.",
    "He said he is tired nti he will rest.",
    "Abeg, can you help me with this work?",
    "I am hungry oo, let's eat jollof rice.",
    "Ny3nkor shopping for clothes later.",
    "m3 fr3wu after church service wai.",
    "She is coming with her friends, you know dada."
]

LOCAL_LANGUAGE_PROMPTS = [
    "Ɛyɛ anɔpa pa wɔ Kumasi.",
    "Me pɛ sɛ me kɔ guare.",
    "Ɔba no da wɔ fie.",
    "Yɛrekɔ adwuma nnɛ.",
    "Meka akyire kyerɛ no."
]

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_metadata[user_id] = {
        "age_range": None,
        "speech_severity": None,
        "origin": None,
        "recordings": []
    }

    user_prompts[user_id] = (
        random.sample(NORMAL_PROMPTS, 3) +
        random.sample(CODE_SWITCHED_PROMPTS, 3) +
        random.sample(LOCAL_LANGUAGE_PROMPTS, 2)
    )
    random.shuffle(user_prompts[user_id])
    user_prompt_index[user_id] = 0

    welcome_text = (
        "👋 Welcome to Project Kasa!\n\n"
        "This project collects voice recordings to improve speech recognition for African speakers.\n"
        "You will record a few short sentences. Each recording helps us understand speech patterns better.\n\n"
        "Let's start with your age range:"
    )

    age_buttons = [
        InlineKeyboardButton("<18", callback_data="age_<18"),
        InlineKeyboardButton("18-24", callback_data="age_18-24"),
        InlineKeyboardButton("25-34", callback_data="age_25-34"),
        InlineKeyboardButton("35-44", callback_data="age_35-44"),
        InlineKeyboardButton("45+", callback_data="age_45+")
    ]
    reply_markup = InlineKeyboardMarkup([age_buttons])
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- Button Callback ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Age
    if data.startswith("age_"):
        user_metadata[user_id]["age_range"] = data.split("_")[1]

        severity_buttons = [
            InlineKeyboardButton("Stammer", callback_data="severity_stammer"),
            InlineKeyboardButton("Stroke", callback_data="severity_stroke"),
            InlineKeyboardButton("Cerebral Palsy", callback_data="severity_cerebral"),
            InlineKeyboardButton("Parkinson's disease", callback_data="severity_parkinson")
        ]
        reply_markup = InlineKeyboardMarkup([severity_buttons])
        await query.edit_message_text(
            f"✅ Age selected: {user_metadata[user_id]['age_range']}\nSelect your speech severity:",
            reply_markup=reply_markup
        )

    # Severity
    elif data.startswith("severity_"):
        severity_map = {
            "severity_stammer": "Stammer",
            "severity_stroke": "Stroke",
            "severity_cerebral": "Cerebral Palsy",
            "severity_parkinson": "Parkinson"
        }
        user_metadata[user_id]["speech_severity"] = severity_map.get(data, "Unknown")

        origin_buttons = [
            InlineKeyboardButton("Kumasi", callback_data="region_kumasi"),
            InlineKeyboardButton("Accra", callback_data="region_accra"),
            InlineKeyboardButton("Volta", callback_data="region_volta"),
            InlineKeyboardButton("North", callback_data="region_north")
        ]
        reply_markup = InlineKeyboardMarkup([origin_buttons])
        await query.edit_message_text(
            f"✅ Severity selected: {user_metadata[user_id]['speech_severity']}\nSelect your region of origin:",
            reply_markup=reply_markup
        )

    # Region
    elif data.startswith("region_"):
        region_map = {
            "region_kumasi": "Kumasi",
            "region_accra": "Accra",
            "region_volta": "Volta",
            "region_north": "North"
        }
        user_metadata[user_id]["origin"] = region_map.get(data, "Unknown")
        await send_prompt(query, user_id)

# --- Send Prompt ---
async def send_prompt(context_object, user_id):
    idx = user_prompt_index[user_id]
    if idx >= TOTAL_RECORDINGS:
        text = "🎉 You have completed all recordings! Thank you for participating. ⭐"
        if hasattr(context_object, "edit_message_text"):
            await context_object.edit_message_text(text)
        else:
            await context_object.reply_text(text)
        save_metadata()
        return

    prompt_text = user_prompts[user_id][idx]
    if prompt_text in CODE_SWITCHED_PROMPTS:
        user_metadata[user_id]["current_prompt_type"] = "code_switched"
    elif prompt_text in LOCAL_LANGUAGE_PROMPTS:
        user_metadata[user_id]["current_prompt_type"] = "local"
    else:
        user_metadata[user_id]["current_prompt_type"] = "normal"

    progress_bar = "⭐" * idx + "☆" * (TOTAL_RECORDINGS - idx)
    text = f"🎤 Prompt {idx + 1}/{TOTAL_RECORDINGS}:\n\n{prompt_text}\n\nProgress: {progress_bar}\nSend your voice message!"

    if hasattr(context_object, "edit_message_text"):
        await context_object.edit_message_text(text)
    else:
        await context_object.reply_text(text)

# --- Voice Handler ---
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_metadata:
        await update.message.reply_text("Please start with /start first.")
        return

    voice: Voice = update.message.voice
    file = await voice.get_file()
    file_name = f"{user_id}_{user_prompt_index[user_id]+1}.ogg"
    file_path = os.path.join("audio", file_name)
    await file.download_to_drive(file_path)

    recording_entry = {
        "file_name": file_name,
        "prompt": user_prompts[user_id][user_prompt_index[user_id]],
        "prompt_type": user_metadata[user_id]["current_prompt_type"]
    }
    user_metadata[user_id]["recordings"].append(recording_entry)

    user_prompt_index[user_id] += 1
    await send_prompt(update.message, user_id)

# --- Save Metadata ---
def save_metadata():
    jsonl_file = os.path.join("metadata", "metadata.jsonl")
    csv_file = os.path.join("metadata", "metadata.csv")

    # JSONL
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for uid, data in user_metadata.items():
            json.dump({"user_id": uid, **data}, f, ensure_ascii=False)
            f.write("\n")

    # CSV
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "age_range", "speech_severity", "origin", "file_name", "prompt", "prompt_type"])
        for uid, data in user_metadata.items():
            for rec in data["recordings"]:
                writer.writerow([
                    uid,
                    data["age_range"],
                    data["speech_severity"],
                    data["origin"],
                    rec["file_name"],
                    rec["prompt"],
                    rec["prompt_type"]
                ])

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.run_polling()
