# Mini Legion Discord Guide Bot

A Discord bot that answers questions about Mini Legion using your game guides and Hugging Face AI.

## Features

- **Ask Questions**: `!ask How do I farm Incense Silk?`
- **Search Guides**: `!search collections`
- **Auto-Updates**: Reads guides directly from GitHub
- **AI-Powered**: Uses Hugging Face Mistral-7B for intelligent answers
- **Free Forever**: Runs on Railway.app's free tier

## Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!ask <question>` | Ask any question about Mini Legion | `!ask How do I upgrade my shirt?` |
| `!search <topic>` | Search for a specific topic | `!search arena rewards` |
| `!reload` | Reload guides from GitHub (Admin only) | `!reload` |
| `!help_guide` | Show help message | `!help_guide` |

## How to Update Your Guides

1. **Clean your new Discord conversations:**
   - Send new conversations to Claude
   - Ask: "Clean this and add it to my Mini Legion guides"
   - Claude will organize and merge the new content

2. **Upload to GitHub:**
   - Go to your repository: `https://github.com/YOUR_USERNAME/mini-legion-guides`
   - Click on `Mini_Legion_Guides_Cleaned.md`
   - Click the pencil icon (Edit)
   - Paste the updated content
   - Scroll down, click "Commit changes"

3. **Reload the bot (Optional):**
   - In Discord, type: `!reload`
   - Or just wait - the bot checks GitHub automatically every time someone asks a question

## Environment Variables (Railway)

These are set in Railway's dashboard:

- `DISCORD_TOKEN` - Your Discord bot token
- `HUGGINGFACE_TOKEN` - Your Hugging Face API token
- `GITHUB_GUIDES_URL` - Raw URL to your guides file

## Troubleshooting

### Bot is offline
- Check Railway dashboard - make sure deployment succeeded
- Check logs in Railway for errors

### Bot doesn't answer questions
- Make sure `GITHUB_GUIDES_URL` is correct
- Try `!reload` command to refresh guides
- Check Railway logs for errors

### Bot says "I don't have information about that"
- The answer might not be in your current guides
- Try `!search <topic>` to see what's in the guides
- Update your guides with new information

## File Structure

```
mini-legion-guides/
├── bot.py                          # Main bot code
├── requirements.txt                # Python dependencies
├── Procfile                        # Railway configuration
├── .env.example                    # Environment variable template
├── README.md                       # This file
└── Mini_Legion_Guides_Cleaned.md   # Your game guides
```

## Tech Stack

- **Discord.py** - Discord bot framework
- **Hugging Face** - AI model (Mistral-7B-Instruct)
- **Railway.app** - Free hosting
- **GitHub** - Guide storage and version control

## Contributing

To add new features or improve the bot:
1. Fork the repository
2. Make your changes
3. Test locally
4. Submit a pull request

## Support

If you need help:
- Check the troubleshooting section above
- Review Railway logs for error messages
- Make sure all environment variables are set correctly

## License

Free to use and modify for your guild/server.
