import discord
import aiosqlite
import openai
import config
import asyncio
from openai import OpenAI
import time
import aiohttp
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
analyzer = SentimentIntensityAnalyzer()
client = OpenAI(api_key=config.OPENAIKEY)
automod_queue = []
automod_enabled = False

async def add_automod_log(db: aiosqlite.Connection, id, user_id: int, model: str, type: str, content: str, reason: str):
    try:
        insert_query = """
            INSERT INTO automod_logs (id, user_id, model, type, content, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        insert_params = (id, user_id, model, type, content, reason)
        await db.execute(insert_query, insert_params)
        await db.commit()
        print(f"Automod log for user ID {user_id} inserted.")
    except Exception as e:
        print(f"Error adding automod log for user ID {user_id}: {e}")
        await db.rollback()

async def set_automod_type(db: aiosqlite.Connection, type: str):
    try:
        update_query = "UPDATE automod SET type = ?"
        update_params = (type,)
        await db.execute(update_query, update_params)
        await db.commit()
        print(f"Automod type set to {type}.")
    except Exception as e:
        print(f"Error setting automod type: {e}")
        await db.rollback()

async def create_base_automod(db: aiosqlite.Connection):
    try:
        insert_query = """
            INSERT INTO automod (
                type, minimum_sexual, enable_sexual, minimum_hate, enable_hate,
                minimum_harassment, enable_harassment, minimum_self_harm, enable_self_harm,
                minimum_sexual_minors, enable_sexual_minors, minimum_hate_threatening, enable_hate_threatening,
                minimum_violence_graphic, enable_violence_graphic, minimum_self_harm_intent, enable_self_harm_intent,
                minimum_self_harm_instructions, enable_self_harm_instructions, minimum_harassment_threatening, enable_harassment_threatening,
                minimum_violence, enable_violence
            ) VALUES (
                'AI', 8, 1, 8, 1,
                8, 1, 8, 1,
                8, 1, 8, 1,
                8, 1, 8, 1,
                8, 1, 8, 1,
                8, 1
            )
        """
        await db.execute(insert_query)
        await db.commit()
        print("Base automod values inserted.")
    except Exception as e:
        print(f"Error inserting base automod values: {e}")
        await db.rollback()

async def get_automod_type():
    async with aiosqlite.connect("./data/database.db") as db:
        query = "SELECT type FROM automod LIMIT 1"
        cursor = await db.execute(query)
        row = await cursor.fetchone()
        if row is None:
            await create_base_automod(db)
            return "AI"
        else:
            return row[0]
        
async def analyze_sentiment(text):
    sentiment_pipeline = pipeline("sentiment-analysis")
    results = sentiment_pipeline([text])  # Analyzing a single text as a list
    return results[0]

async def generate_explanation(sentiment_result, text):
    model_name = "t5-small"  # You can choose a different model if needed
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    label = sentiment_result['label']
    score = sentiment_result['score']
    explanation_prompt = f"Explain why this text is {label.lower()} with a score of {score}: {text}"

    inputs = tokenizer.encode("summarize: " + explanation_prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs, max_length=50, num_beams=4, early_stopping=True)

    explanation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return explanation
        
async def ai_process_message(message):
    text = message['content']
    sentiment_result = await analyze_sentiment(text)
    explanation = await generate_explanation(sentiment_result, text)
    print(f"Text: {text}")
    print(f"Sentiment: {sentiment_result['label']}, Score: {sentiment_result['score']}")
    print(f"Explanation: {explanation}\n")
    
async def process_message(message):
    start_time = time.time()
    try:
        automod_type = await get_automod_type()
        if not automod_enabled:
            print("Automod disabled, skipping message")
            return
        if automod_type == "AI":
            print("Processing message with AI")
            result = await ai_process_message(message)
        elif automod_type == "FILTER":
            print("Processing message with the filter")
            # Add your filter processing logic here
    except Exception as e:
        print(f"Error processing message: {e}")
    finally:
        end_time = time.time()
        print(f"Processed message in {end_time - start_time:.2f} seconds")

async def disable_automod():
    global automod_enabled
    automod_enabled = False
    print("Automod disabled.")

async def enable_automod():
    global automod_enabled
    automod_enabled = True
    print("Automod enabled.")

async def toggle_automod():
    global automod_enabled
    if automod_enabled:
        await disable_automod()
        return "Disabled"
    else:
        await enable_automod()
        return "Enabled"

async def add_to_queue(message):
    automod_queue.append(message)
    if automod_queue:
        msg = automod_queue.pop(0)
        await process_message(msg)
    print(f"Message {message.id} added to automod queue.")

async def check_message(message: discord.Message):
    if message.author.bot or message.author.id in config.AUTOMOD_EXCEPTION_USERS:
        return
    if automod_enabled:
        await add_to_queue(message)
