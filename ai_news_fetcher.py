import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

# Get API keys from environment variables (REQUIRED - no defaults for security)
NEWSDATA_API_KEY = os.environ.get('NEWSDATA_API_KEY')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
GMAIL_ADDRESS = os.environ.get('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')

# Validate that all required environment variables are set
missing_vars = []
if not NEWSDATA_API_KEY:
    missing_vars.append('NEWSDATA_API_KEY')
if not HUGGINGFACE_API_KEY:
    missing_vars.append('HUGGINGFACE_API_KEY')
if not GMAIL_ADDRESS:
    missing_vars.append('GMAIL_ADDRESS')
if not GMAIL_APP_PASSWORD:
    missing_vars.append('GMAIL_APP_PASSWORD')

if missing_vars:
    print("❌ ERROR: Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nPlease set these environment variables before running.")
    print("See .env.example for required variables.")
    sys.exit(1)

# API endpoints
newsdata_url = "https://newsdata.io/api/1/news"
huggingface_api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

# Calculate 24 hours ago
twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

# Parameters for news request
params = {
    "apikey": NEWSDATA_API_KEY,
    "qInTitle": "artificial intelligence OR AI",
    "language": "en",
    "prioritydomain": "top",
    "excludedomain": "nytimes.com,wsj.com,ft.com,washingtonpost.com,bloomberg.com",
    "size": 10
}

def scrape_article(article_url):
    """Attempt to scrape article text from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all paragraphs
        paragraphs = soup.find_all('p')
        article_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        return article_text if article_text else "No text found"
        
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_with_bart(text, fallback_description=""):
    """Use BART to summarize the article, with fallback to description"""
    try:
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
        }
        
        # Ensure text is a string and not None
        text = text or ""
        
        # Truncate text if too long (BART has limits)
        max_length = 1024
        if len(text) > max_length:
            text = text[:max_length]
        
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": 300,
                "min_length": 80,
                "do_sample": False
            }
        }
        
        response = requests.post(huggingface_api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                summary = result[0].get('summary_text', '')
                if summary:
                    return summary
        
        # If we get here, something failed - use fallback
        print(f"  ⚠️  BART failed (status {response.status_code}), using description as fallback")
        return fallback_description if fallback_description else "Summary unavailable"
            
    except Exception as e:
        print(f"  ⚠️  BART error: {e}, using description as fallback")
        return fallback_description if fallback_description else "Summary unavailable"
    
def rate_interestingness(title, description, summary):
    """Simple heuristic to rate article interestingness (1-10)"""
    score = 5  # Base score
    
    # Keywords that indicate interesting business/tech AI news
    interesting_keywords = [
        'breakthrough', 'launch', 'unveil', 'billion', 'investment', 
        'regulation', 'ban', 'revolutionary', 'first', 'major', 
        'announces', 'partnership', 'acquire', 'startup', 'unicorn'
    ]
    
    # Safely combine all text, ensuring no None values
    title = title or ''
    description = description or ''
    summary = summary or ''
    text = (title + ' ' + description + ' ' + summary).lower()
    
    # Add points for interesting keywords
    for keyword in interesting_keywords:
        if keyword in text:
            score += 1
    
    # Cap at 10
    return min(score, 10)

def send_email_digest(articles):
    """Send email digest with top articles"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"AI News Digest - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = GMAIL_ADDRESS
        
        # Create HTML email
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .article {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }}
                .score {{ background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .source {{ color: #666; font-size: 0.9em; }}
                .summary {{ margin: 10px 0; background-color: #f9f9f9; padding: 10px; border-left: 3px solid #4CAF50; }}
                .link {{ display: inline-block; margin-top: 10px; padding: 8px 15px; background-color: #008CBA; color: white; text-decoration: none; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Your Daily AI Business News Digest</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>
            <div style="padding: 20px;">
                <p>Good morning! Here are the top {len(articles)} AI business articles from the past 24 hours:</p>
        """
        
        for i, article in enumerate(articles, 1):
            # Safely get values with defaults
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown source')
            published = article.get('published', 'Unknown date')
            summary = article.get('summary', 'No summary available')
            link = article.get('link', '#')
            interest_score = article.get('interest_score', 0)
            
            html += f"""
                <div class="article">
                    <h2>{i}. {title}</h2>
                    <p class="source">
                        <span class="score">Interest: {interest_score}/10</span> | 
                        Source: {source} | 
                        Published: {published}
                    </p>
                    <div class="summary">
                        <strong>Summary:</strong> {summary}
                    </div>
                    <a href="{link}" class="link">Read Full Article →</a>
                </div>
            """
        
        html += """
            </div>
            <div style="text-align: center; padding: 20px; color: #666; font-size: 0.9em;">
                <p>This digest was automatically generated by your AI News Fetcher</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email digest sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

# Main execution
print("=" * 80)
print("STEP 1: Fetching AI news articles from newsdata.io...")
print("=" * 80)
response = requests.get(newsdata_url, params=params)

if response.status_code == 200:
    data = response.json()
    
    # Words that indicate medical/health (we want to exclude these)
    exclude_keywords = ['medical', 'health', 'healthcare', 'hospital', 'patient', 
                       'clinical', 'disease', 'diagnosis', 'treatment', 'doctor',
                       'medicine', 'pharmaceutical', 'drug', 'therapy', 'cancer']
    
    # Filter articles
    filtered_articles = []
    if data.get('results'):
        for article in data['results']:
            pub_date_str = article.get('pubDate')
            if not pub_date_str:
                continue
                
            # Parse the date
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                print(f"  ⚠️  Could not parse date: {pub_date_str}")
                continue
            
            # Check if it's from last 24 hours
            if pub_date.replace(tzinfo=None) < twenty_four_hours_ago:
                continue
            
            # Get title and description for checking - FIXED: Handle None values properly
            title = (article.get('title') or '').lower()
            description = (article.get('description') or '').lower()
            full_text = title + ' ' + description
            
            # Skip ONLY if it contains medical/health keywords
            if any(keyword in full_text for keyword in exclude_keywords):
                continue
            
            filtered_articles.append(article)
    
    # Limit to 10 articles
    filtered_articles = filtered_articles[:10]
    
    print(f"\n✅ Found {len(filtered_articles)} articles\n")
    
    print("=" * 80)
    print("STEP 2: Scraping full text from articles...")
    print("=" * 80)
    
    # Scrape full text for each article
    articles_with_text = []
    for i, article in enumerate(filtered_articles, 1):
        # Safely get title with default
        article_title = article.get('title', 'No title')
        print(f"\n[{i}/{len(filtered_articles)}] {article_title[:70]}...")
        
        # Scrape the article - safely get link
        article_link = article.get('link')
        if not article_link:
            print(f"  ⚠️  Skipping - no link available")
            continue
            
        full_text = scrape_article(article_link)
        text_length = len(full_text) if not full_text.startswith('Error') else 0
        
        # Skip articles with very little text (likely paywalled)
        if text_length < 200:
            print(f"  ⚠️  Skipping - too little text (likely paywalled)")
            continue
        
        print(f"  ✅ Scraped {text_length:,} characters")
        
        articles_with_text.append({
            'original': article,
            'full_text': full_text
        })
        
        # Be respectful - wait 2 seconds between requests
        if i < len(filtered_articles):
            time.sleep(2)
    
    print(f"\n✅ Successfully scraped {len(articles_with_text)} articles")
    
    print("\n" + "=" * 80)
    print("STEP 3: Summarizing articles with BART...")
    print("=" * 80)
    
    # Summarize each article
    analyzed_articles = []
    for i, item in enumerate(articles_with_text, 1):
        article = item['original']
        full_text = item['full_text']
        
        # Safely get title
        article_title = article.get('title', 'No title')
        print(f"\n[{i}/{len(articles_with_text)}] Summarizing: {article_title[:60]}...")
        
        # Get summary from BART - safely handle description
        article_description = article.get('description') or ''
        summary = summarize_with_bart(full_text, article_description)
        print(f"  Summary: {summary[:100]}...")
        
        # Rate interestingness - safely get all fields
        interest_score = rate_interestingness(
            article.get('title') or '',
            article_description,
            summary
        )
        print(f"  Interest Score: {interest_score}/10")
        
        # Create enhanced article object - safely get all fields
        analyzed_article = {
            'title': article.get('title', 'No title'),
            'source': article.get('source_id', 'Unknown source'),
            'published': article.get('pubDate', 'Unknown date'),
            'link': article.get('link', ''),
            'description': article_description,
            'full_text': full_text,
            'summary': summary,
            'interest_score': interest_score,
            'scraped_at': datetime.now().isoformat()
        }
        
        analyzed_articles.append(analyzed_article)
        
        # Wait 1 second between API calls
        time.sleep(1)
    
    # Sort by interest score (highest first)
    analyzed_articles.sort(key=lambda x: x['interest_score'], reverse=True)
    
    # Save files
    if analyzed_articles:
        filename_all = f"ai_news_all_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename_all, 'w', encoding='utf-8') as f:
            json.dump(analyzed_articles, f, indent=2, ensure_ascii=False)
        
        # Save TOP 5 most interesting
        top_articles = analyzed_articles[:5]
        filename_top = f"ai_news_top5_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename_top, 'w', encoding='utf-8') as f:
            json.dump(top_articles, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📄 Saved {len(analyzed_articles)} articles to: {filename_all}")
        print(f"📄 Saved top 5 articles to: {filename_top}")
        
        print("\n" + "=" * 80)
        print("STEP 4: Sending email digest...")
        print("=" * 80)
        
        # Send email with top 5 articles
        send_email_digest(top_articles)
        
        print("\n" + "=" * 80)
        print("TOP 5 MOST INTERESTING ARTICLES:")
        print("=" * 80)
        for i, article in enumerate(top_articles, 1):
            print(f"\n{i}. [{article['interest_score']}/10] {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Summary: {article['summary']}")
    else:
        print("\n⚠️  No articles found.")
        
else:
    print(f"Error: {response.status_code}")
    print(response.text)
