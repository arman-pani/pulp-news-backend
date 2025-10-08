from datetime import datetime, timezone
import json
from typing import Any, Dict, List

import google.genai as genai
from database.postsql_db_connection import Article
from config.config import config

# Use API key from config
GEMINI_API_KEY = config.GEMINI_API_KEY


# Get permanent categories from config
PERMANENT_CATEGORIES = config.PERMANENT_CATEGORIES


def summarize_articles_batch(articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize all articles at once using DeepSeek V3.1 via OpenRouter (with structured outputs)."""
    if not articles_data:
        return []

    try:
        # Create categories string for the prompt
        categories_str = ", ".join(PERMANENT_CATEGORIES)
        
        client = genai.Client(api_key=GEMINI_API_KEY)

        system_instruction = f"""
        You are a professional news writer. You will be given a list of news articles in JSON format from multiple Odisha news sources.

        For EACH article, please:
        1. Create a concise title (max 8 words)
        2. Write a very short summarised content (50 words max)
        3. Categorize the article using ONLY one of these categories: {categories_str}
        4. Keep the essential facts accurate

        Return ONLY a JSON array where each object has:
        - source_url (same as original data's "url")
        - title (concise)
        - content (shortened version of original content, 50 words max)
        - category (must be one of: {categories_str})
        """

        articles_json = json.dumps(articles_data, ensure_ascii=False, indent=2)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=articles_json,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 20,
                "candidate_count": 1,
            },
        )   

        response_text = response.text.strip()
        
        # Clean the response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        try:
            summarized_articles = json.loads(response_text.strip())
            
            result = []
            for original_article in articles_data:
                source_url = original_article["url"]
                summarized = next((a for a in summarized_articles if a.get("source_url") == source_url), None)
                
                if summarized:
                    # Format authors as a string
                    authors_str = ", ".join(original_article["authors"]) if isinstance(original_article["authors"], list) else str(original_article["authors"])
                    
                    article = Article(
                        source_name= original_article["source_name"],
                        source_url= source_url,
                        title= summarized.get("title", original_article["original_title"]),
                        author= authors_str,
                        published_at= original_article["publish_date"],
                        image_url= original_article["image_url"],
                        content= summarized.get("content"),
                        category= summarized.get("category", "General"),
                        created_at=datetime.now(timezone.utc)
                    )

                    result.append(article)
                    
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response: {e}")
            print(f"Response was: {response.text}")
            return []
            
    except Exception as e:
        print(f"Error in batch summarization: {e}")
        return []
