import os
import asyncio
from openai import OpenAI
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
from pydantic import BaseModel, Field

# Set up OpenAI API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get CryptoPanic API auth token from environment variable
auth_token = os.getenv('CRYPTOPANIC_AUTH_TOKEN')

class Article(BaseModel):
    title: str = Field(..., description="Title of the article.")
    short_description: str = Field(..., description="Short description or summary of the article.")
    category: str = Field(..., description="Category or topic of the article.")

async def crawl_multiple_urls(urls):
    async with AsyncWebCrawler(verbose=True) as crawler:
        tasks = [crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
        provider= "openai/gpt-4o-mini", api_token = os.getenv('OPENAI_API_KEY'), 
        schema=Article.model_json_schema(),
        extraction_type="schema",
        apply_chunking =False,
        instruction="""
From the crawled content, extract all articles presented on the page. For each article, extract the following details:

1. **Title** of the article.
2. **Short description** or summary of the article.
3. **Category** or topic of the article.
4. **URL** of the article.

Organize the extracted information into a JSON object matching the provided schema, which includesa list of `articles`. Each article should have `title`, `short_description`, `category` and `url` fields.

**Example format:**

```json
  [
    {
        "title": "Article Title 1",
        "short_description": "Short description of article 1.",
        "category": "Category of article 1",
        "url": "https://example.com/article-1"
    },
    {
        "title": "Article Title 2",
        "short_description": "Short description of article 2.",
        "category": "Category of article 2",
        "url": "https://example.com/article-2"
    }
  ]
Ensure that all extracted information is accurate and complete. """),
            chunking_strategy=RegexChunking(),
            bypass_cache=True
        ) for url in urls]
        results = await asyncio.gather(*tasks)
    return results

def is_related_to_topic(article, topic):
    content = f"{article['title']}\n{article['short_description']}\n{article['category']}"
    prompt = f"Determine if the following text is related to the topic '{topic}'. Respond with only 'Yes' or 'No'.\n\nText: {content[:1000]}..."
    response = openai_client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that determines if text is related to a given topic."},
        {"role": "user", "content": prompt}
    ])
    return response.choices[0].message.content.strip().lower() == "yes"