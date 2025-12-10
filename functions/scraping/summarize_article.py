from datetime import datetime, timezone
import json
from typing import Any, Dict, List

import google.genai as genai
from database.postsql_db_connection import Article
from config.config import config
from openai import OpenAI   # ✅ Correct SDK

# Use API key from config
# GEMINI_API_KEY = config.GEMINI_API_KEY

# Use API key from config (you'll need to add this in your config)
OPENROUTER_API_KEY = config.OPENROUTER_API_KEY

# Choose your OpenRouter model (e.g. "google/gemini-2.0-flash-001" or "openrouter/auto")
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# Get permanent categories from config
PERMANENT_CATEGORIES = config.PERMANENT_CATEGORIES


# def summarize_articles_batch(articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     if not articles_data:
#         return []

#     try:
#         # Create categories string for the prompt
#         categories_str = ", ".join(PERMANENT_CATEGORIES)
        
#         client = genai.Client(api_key=GEMINI_API_KEY)

#         system_instruction = f"""
#         You are a professional news writer. You will be given a list of news articles in JSON format from multiple Odisha news sources.

#         For EACH article, please:
#         1. Create a concise title (max 8 words)
#         2. Write a very short summarised content (50 words min)
#         3. Categorize the article using ONLY one of these categories: {categories_str}
#         4. Keep the essential facts accurate

#         Return ONLY a JSON array where each object has:
#         - source_url (same as original data's "url")
#         - title (concise)
#         - content (shortened version of original content, 50 words min)
#         - category (must be one of: {categories_str})
#         """

#         articles_json = json.dumps(articles_data, ensure_ascii=False, indent=2)

#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=articles_json,
#             config={
#                 "system_instruction": system_instruction,
#                 "temperature": 0.2,
#                 "top_p": 0.9,
#                 "top_k": 20,
#                 "candidate_count": 1,
#             },
#         )   

#         response_text = response.text.strip()
        
#         # Clean the response
#         if response_text.startswith('```json'):
#             response_text = response_text[7:]
#         if response_text.startswith('```'):
#             response_text = response_text[3:]
#         if response_text.endswith('```'):
#             response_text = response_text[:-3]

#         try:
#             summarized_articles = json.loads(response_text.strip())
            
#             result = []
#             for original_article in articles_data:
#                 source_url = original_article["url"]
#                 summarized = next((a for a in summarized_articles if a.get("source_url") == source_url), None)
                
#                 if summarized:
#                     # Format authors as a string
#                     authors_str = ", ".join(original_article["authors"]) if isinstance(original_article["authors"], list) else str(original_article["authors"])
                    
#                     article = Article(
#                         source_name= original_article["source_name"],
#                         source_url= source_url,
#                         title= summarized.get("title", original_article["original_title"]),
#                         author= authors_str,
#                         published_at= original_article["publish_date"],
#                         image_url= original_article["image_url"],
#                         content= summarized.get("content"),
#                         category= summarized.get("category", "General"),
#                         created_at=datetime.now(timezone.utc)
#                     )

#                     result.append(article)
                    
#             return result
            
#         except json.JSONDecodeError as e:
#             print(f"Failed to parse Gemini response: {e}")
#             print(f"Response was: {response.text}")
#             return []
            
#     except Exception as e:
#         print(f"Error in batch summarization: {e}")
#         return []

def summarize_articles_batch(articles_data: List[Dict[str, Any]]) -> List[Article]:
    if not articles_data:
        return []

    try:
        categories_str = ", ".join(PERMANENT_CATEGORIES)

        system_instruction = f"""
        You are a professional news writer. You will be given a list of news articles in JSON format from multiple Odisha news sources.

        For EACH article, please:
        1. Create a concise title (max 8 words)
        2. Write a very short summarised content (50 words min)
        3. Categorize the article using ONLY one of these categories: {categories_str}
        4. Keep the essential facts accurate
        
        Return a JSON object with an "articles" key containing an array where each object has:
        - source_url (same as original data's "url")
        - title (concise)
        - content (shortened version of original content, 50 words min)
        - category (must be one of: {categories_str})
        
        Example format:
        {{
            "articles": [
                {{"source_url": "...", "title": "...", "content": "...", "category": "..."}}
            ]
        }}
        """

        articles_json = json.dumps(articles_data, ensure_ascii=False, indent=2)

        # ✅ OpenRouter Client via OpenAI SDK
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        # Define JSON schema (for documentation and future strict mode support)
        # Note: Free models may not support strict json_schema, so we use json_object mode
        response_schema = {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "description": "Array of summarized news articles",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_url": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {"type": "string"}
                        },
                        "required": ["source_url", "title", "content", "category"]
                    }
                }
            },
            "required": ["articles"]
        }

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": articles_json},
            ],
            response_format={"type": "json_object"},  # ✅ Use json_object for compatibility
            temperature=0.2,
            top_p=0.9,
        )

        response_text = response.choices[0].message.content.strip()
        print(f"📝 Raw API response length: {len(response_text)} characters")

        # Clean markdown fences if present (free models may still wrap JSON)
        if "```json" in response_text:
            # Extract content between ```json and ```
            start_idx = response_text.find("```json") + 7
            end_idx = response_text.find("```", start_idx)
            if end_idx != -1:
                response_text = response_text[start_idx:end_idx].strip()
                print("🧹 Cleaned markdown fence from response")
        elif "```" in response_text:
            # Handle generic code fences
            start_idx = response_text.find("```") + 3
            end_idx = response_text.find("```", start_idx)
            if end_idx != -1:
                response_text = response_text[start_idx:end_idx].strip()
                print("🧹 Cleaned generic fence from response")

        # Parse JSON directly (json_object mode ensures JSON output)
        try:
            response_json = json.loads(response_text.strip())
            # Extract articles array from the response object
            if isinstance(response_json, dict) and "articles" in response_json:
                summarized_articles = response_json["articles"]
                print(f"✅ Parsed {len(summarized_articles)} articles from structured response")
            elif isinstance(response_json, list):
                # Fallback: if response is already an array (backward compatibility)
                summarized_articles = response_json
                print(f"✅ Parsed {len(summarized_articles)} articles from array response")
            else:
                print(f"❌ Unexpected response format: {type(response_json)}")
                print(f"Response keys: {response_json.keys() if isinstance(response_json, dict) else 'N/A'}")
                return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse OpenRouter response: {e}")
            print(f"Response was: {response_text}")
            return []

        result: List[Article] = []

        for original_article in articles_data:
            source_url = original_article["url"]

            summarized = next(
                (a for a in summarized_articles if a.get("source_url") == source_url),
                None,
            )

            if summarized:
                authors_str = (
                    ", ".join(original_article["authors"])
                    if isinstance(original_article["authors"], list)
                    else str(original_article["authors"])
                )

                article = Article(
                    source_name=original_article["source_name"],
                    source_url=source_url,
                    title=summarized.get(
                        "title", original_article.get("original_title")
                    ),
                    author=authors_str,
                    published_at=original_article["publish_date"],
                    image_url=original_article["image_url"],
                    content=summarized.get("content"),
                    category=summarized.get("category", "General"),
                    created_at=datetime.now(timezone.utc),
                )

                result.append(article)

        return result

    except Exception as e:
        print(f"Error in batch summarization (OpenRouter): {e}")
        return []