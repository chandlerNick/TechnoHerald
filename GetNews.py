import feedparser
import requests
import re

## --- CONFIG ---
API_URL = "https://api-inference.huggingface.co/models/microsoft/prophetnet-large-uncased"
headers = {"Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY"}  # Replace with your Hugging Face API key

# --- Helpers --- 
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def get_news(news_source: str):
    """Fetches news from a given RSS feed URL."""
    try:
        feed = feedparser.parse(news_source)
        news_items = []

        for entry in feed.entries[:3]:
            news_item = {
                'title': entry.title,
                'link': entry.link,
                'published': entry.published,
                'summary': entry.summary
            }
            news_items.append(news_item)

        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def summarize_text(text: str) -> str:
    """Summarizes the given text using a Hugging Face model."""
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['summary_text']
    else:
        print(f"Error summarizing text: {response.status_code}")
        return text



def main():
    print("Reading news...")
    # Fetch news
    bbc_news = get_news("https://feeds.bbci.co.uk/news/rss.xml")  # RSS feed url
    print("BBC news fetched")
    reuters_news = get_news("https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen")
    print("Reuters news fetched")
    pew_news = get_news("https://www.pewresearch.org/feed/")
    print("Pew news fetched")
    bloomberg_news = get_news("https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com&hl=en-US&gl=US&ceid=US:en")
    print("Bloomberg news fetched")
    aljazeera_news = get_news("https://www.aljazeera.com/xml/rss/all.xml")
    print("Al Jazeera news fetched")
    
    news_sources = {"bbc_news": bbc_news, "reuters_news": reuters_news, "pew_news":pew_news, "bloomberg_news":bloomberg_news, "aljazeera_news":aljazeera_news}
    
    per_source_summaries = {}
    
    # iterate through each news source
    for news_name, news in news_sources.items():
        per_source_summaries[news_name] = []  # to store summaries for this source
        news_info_list = []  # to store news info for each news article for this source
        
        # iterate through each news item
        for item in news:
            # summarize the news item
            print(f"Source: {news_name}")
            print(f"Title: {item['title']}")
            print(f"Link: {item['link']}")
            print(f"Published: {item['published']}")
            print(f"Summary: {item['summary']}")
            print("-" * 80)
            print("\n")
            news_info_list.append(f"{strip_html_tags(item['title'])};{strip_html_tags(item['published'])};{strip_html_tags(item['summary'])}")

        # summarize the news items for the current source
        all_news = "|".join(news_info_list)
        summary = summarize_text(all_news)
        print(f"Summary for {news_name}: {summary}")
        per_source_summaries[news_name] = summary
        print("-" * 80)
        
    # Print and collect all summaries
    print("Summaries for all sources:")
    summaries = []
    for source, summary in per_source_summaries.items():
        print(f"{source}: {summary}")
        print("-" * 80)
        summaries.append(f"{source}: {summary}")
    print("\n")
    total_summary = summarize_text("Here are summaries of headlines from various news sources: " + "\n".join(summaries) + "\nSummarize the key themes and topics that are important for the economy in a few sentences drawing connections between the sources.")
    print("Total Summary:", total_summary)


if __name__ == "__main__":
    main()