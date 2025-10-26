# 🤖 AI News Digest - Automated Daily Newsletter

An automated system that fetches, analyzes, and delivers the top AI business news articles directly to your inbox every morning.

## ✨ Features

- 📰 Fetches latest AI news from NewsData.io
- 🔍 Web scraping to get full article text
- 🤖 AI-powered summarization using Hugging Face BART model
- 📊 Intelligent rating system to rank article importance
- 📧 Beautiful HTML email digest sent daily
- ⏰ Runs automatically every morning via GitHub Actions
- 🎯 Filters out medical/health AI news to focus on business & tech

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-news-digest.git
cd ai-news-digest
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

You'll need to get API keys from these services:

#### NewsData.io API Key
1. Go to https://newsdata.io/
2. Sign up for a free account
3. Copy your API key

#### Hugging Face API Key
1. Go to https://huggingface.co/settings/tokens
2. Create a new token
3. Copy the token

#### Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new app password
3. Copy the 16-character password

### 4. Configure Environment Variables

**For Local Testing:**

Create a `.env` file (already in `.gitignore`):

```bash
cp .env.example .env
```

Edit `.env` and add your actual keys:

```
NEWSDATA_API_KEY=your_actual_key_here
HUGGINGFACE_API_KEY=your_actual_token_here
GMAIL_ADDRESS=youremail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_password
```

**For GitHub Actions:**

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these four secrets:
   - `NEWSDATA_API_KEY`
   - `HUGGINGFACE_API_KEY`
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`

### 5. Run Locally (Testing)

```bash
python ai_news_fetcher/ai_news_fetcher.py
```

### 6. Schedule Automation

The workflow is already configured in `.github/workflows/daily-digest.yml` to run daily at 7 AM Central Time.

To manually trigger:
1. Go to **Actions** tab on GitHub
2. Click **Daily AI News Digest**
3. Click **Run workflow**

## 📁 Project Structure

```
ai-news-digest/
├── .github/
│   └── workflows/
│       └── daily-digest.yml    # GitHub Actions workflow
├── ai_news_fetcher/
│   └── ai_news_fetcher.py      # Main script
├── .env.example                 # Template for environment variables
├── .gitignore                   # Prevents committing sensitive files
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔒 Security

- ✅ No credentials are hardcoded
- ✅ All sensitive data in environment variables
- ✅ `.env` file is in `.gitignore`
- ✅ GitHub Secrets used for automation

**Important:** Never commit your `.env` file or actual API keys to Git!

## 📊 How It Works

1. **Fetch**: Gets latest AI articles from NewsData.io API
2. **Filter**: Removes medical/health articles and paywalled content
3. **Scrape**: Extracts full text from article URLs
4. **Summarize**: Uses BART AI model to create concise summaries
5. **Rate**: Scores articles based on business relevance (1-10)
6. **Send**: Emails top 5 articles in beautiful HTML format

## 📧 Email Preview

The digest includes:
- Article title and source
- Interest score (1-10)
- AI-generated summary
- Link to full article
- Clean, mobile-friendly design

## 🛠️ Technologies Used

- **Python 3.11**
- **NewsData.io API** - News aggregation
- **Hugging Face Transformers** - AI summarization (BART)
- **BeautifulSoup** - Web scraping
- **GitHub Actions** - Automation
- **Gmail SMTP** - Email delivery

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

## ⚠️ Troubleshooting

**Workflow not running?**
- Check that GitHub Actions is enabled
- Verify all secrets are set correctly
- Check the Actions tab for error logs

**Not receiving emails?**
- Verify Gmail app password is correct
- Check spam folder
- Ensure 2FA is enabled on Gmail account

**API errors?**
- Check that API keys are valid
- Verify you haven't exceeded rate limits
- NewsData.io free tier has limits

## 📞 Support

If you find this project helpful, please give it a ⭐ on GitHub!

---

Built with ❤️ for staying up-to-date with AI business news
