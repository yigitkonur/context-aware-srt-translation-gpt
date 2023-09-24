import os
import time
import math
import asyncio
import logging
import traceback
import requests
import pysrt
import spacy
import openai
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from aiolimiter import AsyncLimiter
from rich.logging import RichHandler
from rich.console import Console
from tenacity import retry, stop_after_attempt

# FastAPI Instance
app = FastAPI()

# Set up logging with Rich library
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")

# Console for progress monitoring
console = Console()

# Pydantic Models
class TranslationRequest(BaseModel):
    srt_content: str
    source_language: str
    target_language: str

class TranslationResponse(BaseModel):
    translated_srt_content: str
    status: str
    error_message: Optional[str] = None

# OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY', 'xxx')

# DeepL API Key
deepl_api_key = os.getenv('DEEPL_API_KEY', 'xxx')

# Rate Limiter
max_calls = int(os.getenv('MAX_CALLS', 20))
rate_limiter = AsyncLimiter(max_rate=max_calls, time_period=1)  # Adjustable rate limits

# NLP model for sentence tokenization
nlp = spacy.load("en_core_web_sm")

async def translate_with_openai(chunk, source_language, target_language):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": f"You are an AI model specializing in subtitle translation. Your task is to translate three lines of text from a source language to a target language, while retaining the original tone and context. Make sentences short and clear for the target audience, who are young people favoring concise sentences. You can slightly deviate from the original text without altering its meaning too much. Do not modify any timestamps, personal information, or disrupt the original format.\r\n\r\nHere's the input format:\r\n\r\n```\r\n1) first string to translate\r\n2) second string to translate\r\n3) third string to translate\r\n```\r\n\r\nAnd the expected output:\r\n\r\n```\r\n1) translated first string\r\n2) translated second string\r\n3) translated third string\r\n```\r\n\r\nWhile translating, keep in mind:\r\n\r\n- Source language for the translation: {source_language}\r\n- Target language for the translation: {target_language}\r\n\r\nFrom now on, the 'user' will provide the text directly in three lines. You should return your translation preserving its format. If the user\u2019s input isn't three lines, return at least 3 lines that can be even a new line without content but the output must be having three lines. Use plain Turkish that everyone can understand in translation. Please try to understand the context between three lines and respect to flow of subtitle by deeply understanding context before translating."},
            {"role": "user", "content": f"1) I think you guys know me and obviously the prime minister, but if you guys could introduce yourselves and say a bit about you and, you've done both done amazing things, so please don't be shy.\r\n2) Greg Brockman from OpenAI: Sure thing.\r\n3) So I'm Greg Brockman."},
            {"role": "assistant", "content": f"1) San\u0131r\u0131m beni ve tabii ki ba\u015Fbakan\u0131 tan\u0131yorsunuz. Ama siz kendinizi tan\u0131tabilir ve hakk\u0131n\u0131zda biraz bilgi verebilir misiniz? \u0130kiniz de harika \u015Feyler ba\u015Fard\u0131n\u0131z, l\u00FCtfen \u00E7ekinmeden konu\u015Fun.\r\n2) Greg Brockman \/ OpenAI'dan: Tabii ki!\r\n3) Evet, ben Greg Brockman. "},
            {"role": "user", "content": f"1) Greg Brockman from OpenAI: did it.\r\n2) We literally had an intern in 20, 2016.\r\n3) So our very first summer who we had this conversation about."},
            {"role": "assistant", "content": f"1) OpenAI'dan Greg Brockman: biz yapm\u0131\u015Ft\u0131k!\r\n2) 2016'da tam 20 ya\u015F\u0131nda bi tane harbi stajyerimiz vard\u0131\r\n3) Bu muhabbeti yapt\u0131\u011F\u0131m\u0131zda OpenAI'daki ilk yaz aylar\u0131m\u0131zd\u0131"},
            {"role": "user", "content": f"1) The Max's book takes you to the existential question of whether, you\r\n2) project basically machine intelligence or human intelligence into the cosmos,\r\n3) human intelligence turned into machine intelligence into the cosmos and so on."},
            {"role": "assistant", "content": f"1) Max'\u0131n kitab\u0131, bize varolu\u015Fumuzla ilgili \u00E7ok ilgin\u00E7 bir soru soruyor.\r\n2) Biz evrene robot zekas\u0131 m\u0131, yoksa insan zekas\u0131 m\u0131 b\u0131rakaca\u011F\u0131z? \r\n3) Yoksa insan zekas\u0131 bundan sonra tamamen robot zakas\u0131 m\u0131 demek olacak?"},   
            {"role": "user", "content": "\n".join(chunk)},
        ]
    )
    response_lines = response['choices'][0]['message']['content'].split("\n", 2)

    # Ensure there are exactly three lines
    while len(response_lines) < 3:
        response_lines.append("")

    return response_lines

def translate_with_deepl(chunk, target_language):
    data = {'text': "\n".join(chunk), 'target_lang': target_language}
    headers = {'Authorization': 'DeepL-Auth-Key ' + deepl_api_key}
    response = requests.post('https://api-free.deepl.com/v2/translate', headers=headers, data=data)
    return response.json()['translations'][0]['text'].split("\n")

async def translate_chunk(chunk, source_language, target_language):
    async with rate_limiter:
        try:
            # Prepend each sentence with its index
            indexed_chunk = [f"{i+1}) {sentence}" for i, sentence in enumerate(chunk)]

            log.debug(f"Translating chunk: {indexed_chunk}")  # Log the chunk

            translated_chunk = await translate_with_openai(indexed_chunk, source_language, target_language)

            # Ensure there are exactly three lines
            while len(translated_chunk) < 3:
                translated_chunk.append("")

            # Strip the index from each translated sentence
            translated_chunk = [sentence.split(') ', 1)[1] if ') ' in sentence else sentence for sentence in translated_chunk]

            log.debug(f"Translated chunk: {translated_chunk}")  # Log the translated chunk

            return translated_chunk
        except Exception as e:
            log.error(f"Error with OpenAI API: {str(e)}. Switching to fallback service: DeepL")

            # Do not prepend the index for DeepL
            translated_chunk = translate_with_deepl(chunk, target_language)

            # Ensure there are exactly three lines
            while len(translated_chunk) < 3:
                translated_chunk.append("Translation not available")

            log.debug(f"Translated chunk with DeepL: {translated_chunk}")  # Log the chunk translated with DeepL

            return translated_chunk


@app.post("/subtitle-translate", response_model=TranslationResponse)
async def translate_subtitle(request: TranslationRequest):
    try:
        log.debug("Received translation request")  # Log the request
        start_time = time.time()
        subs = pysrt.from_string(request.srt_content, encoding='iso-8859-1')
        combined_text = ' '.join([sub.text for sub in subs])
        doc = nlp(combined_text)
        sentences = [line for sub in subs for line in sub.text.split('\n')]

        log.debug(f"Split sentences into {len(sentences)} chunks")  # Add debug log here

        # Create a list to hold all the tasks
        tasks = []
        for i in range(0, len(sentences), 3):
            chunk = sentences[i : i+3]
            # Create a task for each chunk and add it to the tasks list
            tasks.append(asyncio.create_task(translate_chunk(chunk, request.source_language, request.target_language)))

        # Gather all the tasks and run them in parallel
        translated_sentences = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions (i.e., failed translations)
        for i, result in enumerate(translated_sentences):
            if isinstance(result, Exception):
                log.error(f"Failed to translate chunk #{i}: {result}")
                translated_sentences[i] = ["..."] * 3  # Replace the failed translation with "..."

        # Flatten the list of translated sentences
        translated_sentences = [sentence for chunk in translated_sentences for sentence in chunk]

        if len(translated_sentences) != len(sentences):
            log.error("Mismatch in number of sentences in the translated text.")  # Log the mismatch
            # Handle mismatch situations by adding or removing lines as necessary
            while len(translated_sentences) < len(sentences):
                translated_sentences.append("...")
            translated_sentences = translated_sentences[:len(sentences)]

        for i, sub in enumerate(subs):
            if i < len(translated_sentences):
                sub.text = translated_sentences[i]
            else:
                sub.text = ""  # Or some placeholder text

        translated_srt_content = '\n'.join([str(sub) for sub in subs])
        log.debug(f"Translated SRT content: {translated_srt_content}")  # Log the translated SRT content
        log.info(f"Translation completed in {time.time() - start_time} seconds.")

        # Save state every 10 subtitles
        if len(subs) % 10 == 0:
            with open('state.txt', 'w') as f:
                f.write(f"Current position: {len(subs)}\n")
                f.write("Translated text so far:\n" + '\n'.join([str(sub) for sub in subs]))

        return TranslationResponse(
            translated_srt_content=translated_srt_content,
            status="success"
        )
    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
        log.debug(f"Exception details: {traceback.format_exc()}")
        return TranslationResponse(
            translated_srt_content="",
            status="failure",
            error_message=str(e)
        )
