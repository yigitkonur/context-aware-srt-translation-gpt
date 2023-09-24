# Dynamic Context Window Subtitle Translation Service

Welcome to the Dynamic Context Window Subtitle Translation Service! If you value context-aware, linguistically nuanced translations for your subtitles, you're at the right place. This service leverages the exceptional language modeling abilities of OpenAI's GPT-4, along with DeepL as a reliable failover alternative, to provide translation of subtitles with a focus on retaining the natural feel and context of the original dialogue.

## What is a 'Dynamic Context Window'

We present you a smarter way of subtitle translation, the **Dynamic Context Window**. As compared to sentence-by-sentence translations, which lose context, this approach includes the surrounding sentences around the one to be translated. Here is a simplified visualization of our approach:

```plaintext
---------------
| Prev Sentence |
---------------
|   Translate   |
---------------
| Next Sentence |
---------------
```

Each sentence is translated within a window that includes the sentences immediately before and after it, presenting a broader, contextual understanding.

## Main Actors: OpenAI and DeepL

**OpenAI's GPT-4** executes the translations with an enriched sense of context and linguistic nuance as the centerpiece of the operation. In the case of an exception with GPT-4, **DeepL** acts as a reliable failover to ensure the translation persists without any hiccups.

## Features

-    Utilization of OpenAI's GPT model for contextually rich translations.
-    DeepL as a failover option to ensure uninterrupted service.
-    Improved translation nuance with Dynamic Context Window.
-    Exception handling.
-    Regular check-pointing to save the state every 10 subtitles.

## Get Started

After cloning the repository and installing the necessary dependencies, you must set up your environment variables. The service requires necessary API keys:

-   Load `OPENAI_API_KEY` and `DEEPL_API_KEY` environment variables with your OpenAI and DeepL API keys respectively.

The script runs with the powerful capabilities of the Uvicorn ASGI server. You can easily start the FastAPI application using the following command:

```bash
uvicorn main:app --reload
```

Now, the script is all set to roll!

## Requesting Translations

With the server up, make translation requests using a simple CURL command. The API endpoint `/subtitle-translate` exposes a POST route. Here is an example curl request:

```bash
curl -X POST "http://localhost:8000/subtitle-translate" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{\"srt_content\":\"1\n00:02:17,440 --> 00:02:20,375\nSenator, we're making\nour final approach into Coruscant.\n\n2\n00:02:20,476 --> 00:02:22,501\nVery good, Lieutenant.\",\"source_language\":\"en\",\"target_language\":\"tr\"}"
```

The `srt_content` parameter contains the subtitles to translate, `source_language` parameter specifies the current language of the subtitles, and `target_language` parameter specifies the target language for translation.

### Translation Response

A successful translation request will result in a response that includes the translated subtitles in the desired language retaining the original timing and subtitle index. 

Example response:

```bash
{
  "translation": "1\n00:02:17,440 --> 00:02:20,375\nSenatör, Coruscant'a son yaklaşmamızı gerçekleştiriyoruz.\n\n2\n00:02:20,476 --> 00:02:22,501\nÇok iyi, Teğmen."
}
```

## Conclusion

That's it! Now you can use the Dynamic Context Window Subtitle Translation Service, offering a novel method for translating subtitles that preserves context and results in more accurate translations. Happy translating!
