import os
import json
import asyncio
import requests
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
    data = request.get_json(force=True)
    topic = data.get('topic')

    results = asyncio.run(crawl_multiple_urls(urls))

    processed_results = []

    for i, result in enumerate(results):
        if result.success:
            try:
                page_summary = json.loads(result.extracted_content)
                for article in page_summary:
                  if topic:
                    if not is_related_to_topic(article, topic):
                      continue
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

@app.route('/candlestick', methods=['GET'])
def get_candlestick_data():
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    limit = request.args.get('limit', 500)

    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        processed_data = []
        for candle in data:
            processed_data.append({
                "open_time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": candle[6],
                "quote_asset_volume": float(candle[7]),
                "number_of_trades": int(candle[8])
            })
        
        return jsonify({
            "symbol": symbol,
            "interval": interval,
            "data": processed_data
        })
    
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch data from Binance: {str(e)}"}), 500
