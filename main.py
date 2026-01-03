import json
import re
import hashlib
from flask import Flask, render_template, request, Response, stream_with_context
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Single client instance for performance
client = OpenAI()

# In-memory cache for generated articles
article_cache = {}

# Model configuration
MODEL = "gpt-4o"
MAX_TOKENS = 2000

SYSTEM_PROMPT = """You are a Wikipedia article generator. Generate a detailed, well-structured Wikipedia-style article in pure HTML.

REQUIREMENTS:
1. Output ONLY valid HTML - no markdown, no prefixes, no explanations
2. Start directly with content (no wrapper tags needed)
3. Structure:
   - <p> for the introduction paragraph (first paragraph, bold the subject name with <b>)
   - <h2> for major sections
   - <h3> for subsections
   - <p> for paragraphs
   - <ul>/<ol> for lists where appropriate
4. CRITICAL - WIKI LINKS: Use [[double brackets]] around terms that could be their own article (like Wikipedia does). Include 10-20 links throughout the article. Examples:
   - "The [[Roman Empire]] was founded..."
   - "...discovered by [[Albert Einstein]] in..."
   - "...a type of [[mammal]] found in [[Africa]]..."
5. Include these sections:
   - Introduction (2-3 paragraphs)
   - History or Background
   - Key characteristics/aspects
   - See also (use <h2>See also</h2> then <ul> with 5 [[linked topics]])
6. Write in encyclopedic, neutral tone
7. Be comprehensive - aim for 600-800 words"""


def get_cache_key(topic: str) -> str:
    """Generate a cache key for a topic."""
    return hashlib.md5(topic.lower().strip().encode()).hexdigest()


def convert_wiki_links(html_content: str, base_url: str = "/wiki/") -> str:
    """Convert [[wiki links]] to actual HTML links."""
    def replace_link(match):
        topic = match.group(1)
        url_topic = topic.replace(" ", "_")
        return f'<a href="{base_url}{url_topic}">{topic}</a>'

    # Replace all [[topic]] with actual links
    return re.sub(r'\[\[([^\]]+)\]\]', replace_link, html_content)


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/wiki/<path:topic>")
def wiki_page(topic: str):
    """Render a wiki page for a specific topic."""
    # Convert URL-friendly format back to readable
    display_topic = topic.replace("_", " ")
    return render_template("article.html", topic=display_topic)


@app.route("/api/stream/<path:topic>")
def stream_article(topic: str):
    """Stream article generation using Server-Sent Events."""
    display_topic = topic.replace("_", " ")
    cache_key = get_cache_key(display_topic)

    # Check cache first
    if cache_key in article_cache:
        def generate_cached():
            cached_content = article_cache[cache_key]
            # Send cached content in chunks for smooth display
            chunk_size = 100
            for i in range(0, len(cached_content), chunk_size):
                chunk = cached_content[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'cached': True})}\n\n"

        return Response(
            stream_with_context(generate_cached()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    def generate():
        full_content = ""

        try:
            # Use OpenAI Responses API with streaming
            stream = client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                input=f"Generate a Wikipedia-style article about: {display_topic}",
                max_output_tokens=MAX_TOKENS,
                stream=True
            )

            for event in stream:
                # Handle different event types
                if event.type == "response.output_text.delta":
                    delta = event.delta
                    if delta:
                        full_content += delta
                        yield f"data: {json.dumps({'type': 'delta', 'content': delta})}\n\n"

                elif event.type == "response.completed":
                    # Process the complete content - convert [[wiki links]] to HTML
                    processed_content = convert_wiki_links(full_content)

                    # Cache the processed content
                    article_cache[cache_key] = processed_content

                    # Send the final processed version with links
                    yield f"data: {json.dumps({'type': 'final', 'content': processed_content})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'cached': False})}\n\n"

                elif event.type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': str(event.error)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route("/api/search", methods=["POST"])
def search():
    """Handle search form submission - redirects to wiki page."""
    topic = request.form.get("topic", "").strip()
    if not topic:
        return render_template("index.html", error="Please enter a topic")

    # Convert to URL-friendly format
    url_topic = topic.replace(" ", "_")
    return render_template("article.html", topic=topic)


@app.route("/api/clear-cache", methods=["POST"])
def clear_cache():
    """Clear the article cache."""
    article_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


if __name__ == "__main__":
    app.run(debug=True, port=9999)
