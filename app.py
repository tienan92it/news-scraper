import os
import json
import asyncio
from openai import OpenAI
from flask import Flask, request, jsonify
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
from pydantic import BaseModel, Field

app = Flask(__name__)

# Set up OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

urls = [
    'https://decrypt.co/news',
    'https://cryptoslate.com/news/',
    'https://cryptopanic.com/',
    'https://thedefiant.io/latest'
]

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

Organize the extracted information into a JSON object matching the provided schema, which includesa list of `articles`. Each article should have `title`, `short_description`, and `category` fields.

**Example format:**

```json
  [
    {
        "title": "Article Title 1",
        "short_description": "Short description of article 1.",
        "category": "Category of article 1"
    },
    {
        "title": "Article Title 2",
        "short_description": "Short description of article 2.",
        "category": "Category of article 2"
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
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that determines if text is related to a given topic."},
        {"role": "user", "content": prompt}
    ])
    return response.choices[0].message.content.strip().lower() == "yes"

@app.route('/scrape', methods=['POST'])
def scrape_and_summarize():
    data = request.json
    topic = data.get('topic')

    results = asyncio.run(crawl_multiple_urls(urls))

    processed_results = []

    for i, result in enumerate(results):
        if result.success:
            try:
                page_summary = json.loads(result.extracted_content)
                # print(page_summary)
                # if isinstance(page_summary, list) and len(page_summary) > 0:
                #     page_summary = page_summary[0]  # Take the first item if it's a list
                for article in page_summary:
                  if topic:
                  # Check if the content is related to the topic (if provided)
                    if not is_related_to_topic(article, topic):
                      continue  # Skip this result if it's not related to the topic
                  # Add the summary to the processed results
                  processed_results.append({
                      "title": article['title'],
                      "short_description": article['short_description'],
                      "category": article['category']
                        })
                    
            except json.JSONDecodeError:
                processed_results.append({
                    "url": urls[i],
                    "error": "Failed to parse JSON content"
                })
            except Exception as e:
                processed_results.append({
                    "url": urls[i],
                    "error": str(e)
                })
        else:
            processed_results.append({
                "url": urls[i],
                "error": result.error_message
            })

    return jsonify(processed_results)
