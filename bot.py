"""
Mini Legion Guide Bot - IMPROVED VERSION
A Discord bot that answers questions using your game guides and GroqCloud AI.

KEY IMPROVEMENTS:
- Fixed !ask command to actually find relevant content  
- Better search algorithm (filters common words like "how", "do", "i")
- Improved error handling with full traceback
- More debug logging
"""

import os
import discord
from discord.ext import commands
import requests
import json
import traceback

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GITHUB_RAW_URL = os.getenv('GITHUB_GUIDES_URL', 'https://raw.githubusercontent.com/YOUR_USERNAME/mini-legion-guides/main/Mini_Legion_Guides_Cleaned.md')

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable to store guides
GUIDES_CONTENT = ""

def load_guides():
    """Fetch the latest guides from GitHub."""
    try:
        response = requests.get(GITHUB_RAW_URL, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to load guides: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error loading guides: {e}")
        return None

def extract_keywords(text):
    """Extract meaningful keywords from text, filtering out common words."""
    # Common words to ignore
    stop_words = {'how', 'do', 'i', 'the', 'a', 'an', 'is', 'are', 'what', 'where', 
                  'when', 'why', 'who', 'which', 'can', 'should', 'to', 'for', 'of',
                  'in', 'on', 'at', 'from', 'by', 'with', 'get', 'my', 'me', 'you'}
    
    # Split and filter
    words = text.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def find_relevant_sections(guides, question, max_sections=3):
    """
    Find the most relevant sections from guides based on the question.
    THIS IS THE FIX - filters out common words before searching!
    """
    # Extract meaningful keywords (removes "how", "do", "i", etc.)
    keywords = extract_keywords(question)
    
    print(f"DEBUG: Searching for keywords: {keywords}")
    
    if not keywords:
        # Fallback if no keywords
        return [guides[:3000]]
    
    # Split into paragraphs (better granularity than sections)
    paragraphs = [p.strip() for p in guides.split('\n\n') if p.strip()]
    
    # Score each paragraph
    scored_paragraphs = []
    for para in paragraphs:
        para_lower = para.lower()
        
        # Count keyword matches
        score = sum(1 for keyword in keywords if keyword in para_lower)
        
        # Bonus points for exact phrase match
        if question.lower() in para_lower:
            score += 10
        
        # Bonus for having multiple keywords together
        if score >= 2:
            score += 2
        
        if score > 0:
            scored_paragraphs.append((score, para))
    
    # Sort by score (highest first)
    scored_paragraphs.sort(reverse=True, key=lambda x: x[0])
    
    # Take top N paragraphs
    relevant = [para for score, para in scored_paragraphs[:max_sections]]
    
    print(f"DEBUG: Found {len(relevant)} relevant paragraphs")
    if scored_paragraphs:
        print(f"DEBUG: Top score was {scored_paragraphs[0][0]}")
    
    # If no good matches, do a broader search
    if not relevant or (scored_paragraphs and scored_paragraphs[0][0] < 2):
        print("DEBUG: No strong matches, using broader search...")
        # Try searching for ANY keyword
        for para in paragraphs:
            if any(keyword in para.lower() for keyword in keywords):
                relevant.append(para)
                if len(relevant) >= max_sections:
                    break
    
    # Last resort: return beginning of guide
    if not relevant:
        print("DEBUG: No matches found, using guide beginning")
        return [guides[:3000]]
    
    return relevant

def call_groq_api(prompt):
    """Call GroqCloud API for AI response."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",  # Fast, free model
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful Mini Legion game guide assistant. Answer questions based ONLY on the game guides provided. Be concise (2-4 sentences max) and friendly. If you don't have enough information in the guides to answer properly, say so and suggest what you DO know that might be related."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,  # Lower = more focused
        "max_tokens": 350
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    except requests.exceptions.RequestException as e:
        print(f"GroqCloud API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord."""
    global GUIDES_CONTENT
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} server(s)')
    
    # Load guides on startup
    print("Loading guides from GitHub...")
    GUIDES_CONTENT = load_guides()
    if GUIDES_CONTENT:
        print(f"✓ Guides loaded successfully! ({len(GUIDES_CONTENT)} characters)")
    else:
        print("⚠ Warning: Could not load guides. Check GITHUB_GUIDES_URL")

@bot.command(name='ask', help='Ask a question about Mini Legion (e.g., !ask How do I farm Incense Silk?)')
async def ask_question(ctx, *, question):
    """Answer questions using the guides and AI - IMPROVED VERSION."""
    global GUIDES_CONTENT
    
    print(f"DEBUG: Question from {ctx.author}: {question}")
    
    # Send typing indicator
    async with ctx.typing():
        try:
            # Reload guides if empty
            if not GUIDES_CONTENT:
                print("DEBUG: Guides were empty, reloading...")
                GUIDES_CONTENT = load_guides()
            
            if not GUIDES_CONTENT:
                await ctx.send("❌ Sorry, I couldn't load the guides. Please contact the bot admin.")
                return
            
            # Use improved search function (THE FIX!)
            relevant_sections = find_relevant_sections(GUIDES_CONTENT, question, max_sections=3)
            
            # Prepare context for AI (limit total context)
            context = "\n\n".join(relevant_sections)[:4500]  # Leave room for prompt
            print(f"DEBUG: Context length: {len(context)} characters")
            
            # Create prompt for GroqCloud
            prompt = f"""Game Guides Context:
{context}

User Question: {question}

Instructions: Answer the user's question based ONLY on the information provided above from the Mini Legion game guides. Be helpful and specific. If the guides contain the answer, provide it clearly in 2-4 sentences. If you need to reference specific items, strategies, or locations, mention them. If the guides don't have enough information, be honest but offer what related information you do have."""

            print("DEBUG: Calling GroqCloud API...")
            
            # Call GroqCloud API
            answer = call_groq_api(prompt)
            
            print(f"DEBUG: AI Response: {answer[:150]}...")
            
            # If response is too long, truncate
            if len(answer) > 1900:
                answer = answer[:1900] + "..."
            
            # Send response
            embed = discord.Embed(
                title="📚 Mini Legion Guide",
                description=answer,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Question from {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print("CRITICAL ERROR IN ASK_QUESTION:")
            traceback.print_exc()  # This prints full error details
            await ctx.send(f"❌ Sorry, I encountered an error: {str(e)}")

@bot.command(name='reload', help='Reload the guides from GitHub (Admin only)')
@commands.has_permissions(administrator=True)
async def reload_guides(ctx):
    """Reload guides from GitHub (admin command)."""
    async with ctx.typing():
        global GUIDES_CONTENT
        GUIDES_CONTENT = load_guides()
        if GUIDES_CONTENT:
            await ctx.send(f"✅ Guides reloaded! ({len(GUIDES_CONTENT)} characters)")
        else:
            await ctx.send("❌ Failed to reload guides. Check the GitHub URL.")

@bot.command(name='search', help='Search for a topic in the guides (e.g., !search incense silk)')
async def search_guides(ctx, *, search_term):
    """Search for a specific term in the guides."""
    async with ctx.typing():
        if not GUIDES_CONTENT:
            await ctx.send("❌ Guides not loaded. Please contact the bot admin.")
            return
        
        # Find matching sections
        lines = GUIDES_CONTENT.split('\n')
        matches = []
        
        search_lower = search_term.lower()
        for i, line in enumerate(lines):
            if search_lower in line.lower() and line.strip():
                # Get context (2 lines before and after)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                match = '\n'.join(lines[context_start:context_end])
                matches.append(match)
                
                if len(matches) >= 5:  # Increased to 5 matches
                    break
        
        if matches:
            result = "\n\n---\n\n".join(matches)
            if len(result) > 1900:
                result = result[:1900] + "..."
            
            embed = discord.Embed(
                title=f"🔍 Search Results for '{search_term}'",
                description=result,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ No results found for '{search_term}'")

@bot.command(name='help_guide', help='Show available bot commands')
async def help_guide(ctx):
    """Display help information."""
    help_text = """
**Mini Legion Guide Bot Commands:**

`!ask <question>` - Ask any question about Mini Legion
  Example: `!ask How do I farm Incense Silk?`

`!search <topic>` - Search for a specific topic in the guides
  Example: `!search collections`

`!reload` - Reload guides from GitHub (Admin only)

`!help_guide` - Show this help message

**Tips:**
- Be specific with your questions
- The bot uses AI to understand your questions
- Try `!search` for direct text lookup
- Updates automatically when guides are updated on GitHub

**How it works:**
- `!search` finds exact text matches (fast, precise)
- `!ask` uses AI to understand and answer your question (smart, contextual)
    """
    
    embed = discord.Embed(
        title="📖 Mini Legion Bot Help",
        description=help_text,
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use `!help_guide` for usage information.")
    else:
        print(f"Error: {error}")
        traceback.print_exc()
        # Don't send error to user for every error type
        if not isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ An error occurred. Please try again.")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
        print("Set it with: export DISCORD_TOKEN='your_token_here'")
        exit(1)
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY environment variable not set!")
        print("Set it with: export GROQ_API_KEY='your_groq_key_here'")
        exit(1)
    
    print("Starting Mini Legion Guide Bot (Improved Version with GroqCloud)...")
    print("=" * 50)
    bot.run(DISCORD_TOKEN)
