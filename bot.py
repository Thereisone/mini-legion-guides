"""
Mini Legion Guide Bot
A Discord bot that answers questions using your game guides and Hugging Face AI.
"""

import os
import discord
from discord.ext import commands
import requests
from huggingface_hub import InferenceClient

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
GITHUB_RAW_URL = os.getenv('GITHUB_GUIDES_URL', 'https://raw.githubusercontent.com/YOUR_USERNAME/mini-legion-guides/main/Mini_Legion_Guides_Cleaned.md')

# Initialize Hugging Face client
hf_client = InferenceClient(token=HF_TOKEN)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load guides from GitHub
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

# Global variable to store guides
GUIDES_CONTENT = ""

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
    """Answer questions using the guides and AI."""
    
    # Send typing indicator
    async with ctx.typing():
        try:
            # Reload guides if empty
            if not GUIDES_CONTENT:
                global GUIDES_CONTENT
                GUIDES_CONTENT = load_guides()
            
            if not GUIDES_CONTENT:
                await ctx.send("❌ Sorry, I couldn't load the guides. Please contact the bot admin.")
                return
            
            # Search for relevant sections in guides
            question_lower = question.lower()
            relevant_sections = []
            
            # Split guides into sections
            sections = GUIDES_CONTENT.split('\n## ')
            for section in sections:
                if any(keyword in section.lower() for keyword in question_lower.split()):
                    # Take first 2000 chars of relevant section
                    relevant_sections.append(section[:2000])
                    if len(relevant_sections) >= 3:  # Max 3 sections
                        break
            
            # Prepare context for AI
            context = "\n\n".join(relevant_sections) if relevant_sections else GUIDES_CONTENT[:3000]
            
            # Create prompt for Hugging Face
            prompt = f"""You are a helpful Mini Legion game guide assistant. Answer the question based on the game guides provided.

Game Guides Context:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the information in the guides above
- Be concise but helpful (2-4 sentences)
- If the guides don't contain the answer, say "I don't have information about that in the current guides"
- Format your answer in a friendly, Discord-appropriate way
- Don't mention the guides or context in your answer

Answer:"""

            # Call Hugging Face API (using Mistral-7B)
            response = hf_client.text_generation(
                prompt,
                model="mistralai/Mistral-7B-Instruct-v0.2",
                max_new_tokens=300,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.1
            )
            
            # Clean up response
            answer = response.strip()
            
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
            print(f"Error in ask_question: {e}")
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
                # Get context (line before and after)
                context_start = max(0, i - 1)
                context_end = min(len(lines), i + 2)
                match = '\n'.join(lines[context_start:context_end])
                matches.append(match)
                
                if len(matches) >= 3:  # Limit to 3 matches
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
- Updates automatically when guides are updated on GitHub
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
        await ctx.send("❌ An error occurred. Please try again.")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
        exit(1)
    if not HF_TOKEN:
        print("ERROR: HUGGINGFACE_TOKEN environment variable not set!")
        exit(1)
    
    print("Starting Mini Legion Guide Bot...")
    bot.run(DISCORD_TOKEN)
