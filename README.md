# News Scraper API

This project is a Flask-based API that scrapes news articles from multiple cryptocurrency news sources, summarizes them, and optionally filters them by topic. It is designed to be deployed on Render.com.

## Features

- Scrapes news articles from multiple predefined sources
- Extracts article title, short description, and category
- Filters articles by topic (optional)
- Deployed as a web service on Render.com

## Prerequisites

- Python 3.7 or later
- A Render.com account
- An OpenAI API key

## Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/news-scraper-api.git
   cd news-scraper-api
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-openai-api-key'
   ```

5. Run the Flask application locally:
   ```
   python app.py
   ```

The API will be available at `http://localhost:5001`.

## Deployment on Render.com

1. Create a new Web Service on Render.com.

2. Connect your GitHub repository to Render.com.

3. Configure the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. Add the following environment variable in the Render.com dashboard:
   - Key: `OPENAI_API_KEY`
   - Value: Your OpenAI API key

5. Deploy the application.

Render.com will provide you with a URL where your API is accessible.

## Usage

Send a POST request to the `/scrape` endpoint of your deployed API. You can optionally include a `topic` in the request body to filter the results.

Example using curl:

```
curl -X POST -H "Content-Type: application/json" -d '{"topic": "cryptocurrency"}' https://your-render-url.onrender.com/scrape
```

Replace `your-render-url` with the actual URL provided by Render.com.

## Response Format

The API returns a JSON array of articles, each containing:

- `title`: The title of the article
- `short_description`: A brief summary of the article
- `category`: The category or topic of the article

Example response:

```json
[
  {
    "title": "Bitcoin Surges Past $50,000",
    "short_description": "Bitcoin's price has exceeded $50,000 for the first time in three months, signaling a potential bull run.",
    "category": "Markets"
  },
  {
    "title": "New Ethereum Update Reduces Gas Fees",
    "short_description": "The latest Ethereum network update has significantly reduced transaction fees, making the network more accessible.",
    "category": "Technology"
  }
]
```

## Limitations and Considerations

- The API uses OpenAI's GPT model for topic filtering, which may incur costs.
- The current implementation uses `crawl4ai` for web scraping. Ensure you comply with the terms of service of the websites you're scraping.
- Implement proper error handling and rate limiting for production environments.
- Render.com free tier has usage limits. For high-traffic applications, consider upgrading to a paid plan.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.