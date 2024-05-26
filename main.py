import random
from flask import Flask, render_template, request
import anthropic
app = Flask(__name__)
LINK = "http://localhost:9999/generate2/"
MAX_TOKENS = 1000

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.form
    topic = data.get("topic")
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        system="""Please generate a detailed, informative, and well-structured Wikipedia-style page in pure HTML on the following topic: [Insert Topic Here]
        ONLY HTML IS ALLOWED, no prefix or suffix, returned data should be strict HTML, the first word should valid HTML.
        The generated page should include:
        1. A clear and concise introduction that provides an overview of the topic.
        2. Multiple sections and subsections that cover different aspects of the topic in depth. Use appropriate headings and subheadings to organize the content.
        3. Relevant facts, figures, and examples to support the information provided.
        4. Proper formatting, including bold and italic text where necessary, to highlight important points and improve readability.
        5. Internal links to other relevant Wikipedia pages (if applicable), marked with double square brackets [[like this]].
        6. External references and citations to reliable sources, marked with square brackets and numbers [1], [2], etc.
        7. A "See also" section at the end, listing related topics for further reading.
        8. A "References" section at the end, listing all the sources cited in the article using Wikipedia's citation format.
        Please ensure that the generated content is accurate, objective, and written in a clear, encyclopedic style. The page should be comprehensive enough to provide a good understanding of the topic to readers without overwhelming them with excessive detail.
        Remember to break down complex concepts into easily understandable language and maintain a neutral point of view throughout the article.
        """,
        messages=[
            {"role": "user", "content": f"Generate a Wikipedia-style page on {topic}."}
        ]
    )
    # print(message)
    x = message.model_dump(include={"content":True})
    changed = make_words_links(x["content"][0]["text"])
    print(changed)
    return changed

@app.route("/generate2/<topic>", methods=["GET"])
def generate2(topic):
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        system="""Please generate a detailed, informative, and well-structured Wikipedia-style page in pure HTML on the following topic: [Insert Topic Here]
        ONLY HTML IS ALLOWED WITHOUT ANY LINKS, no prefix or suffix, returned data should be strict HTML, the first word should valid HTML.
        The generated page should include:
        1. A clear and concise introduction that provides an overview of the topic.
        2. Multiple sections and subsections that cover different aspects of the topic in depth. Use appropriate headings and subheadings to organize the content.
        3. Relevant facts, figures, and examples to support the information provided.
        4. Proper formatting, including bold and italic text where necessary, to highlight important points and improve readability.
        5. Internal links to other relevant Wikipedia pages (if applicable), marked with double square brackets [[like this]].
        6. External references and citations to reliable sources, marked with square brackets and numbers [1], [2], etc.
        7. A "See also" section at the end, listing related topics for further reading.
        8. A "References" section at the end, listing all the sources cited in the article using Wikipedia's citation format.
        9. Add no hrefs from your side.
        Please ensure that the generated content is accurate, objective, and written in a clear, encyclopedic style. The page should be comprehensive enough to provide a good understanding of the topic to readers without overwhelming them with excessive detail.
        Remember to break down complex concepts into easily understandable language and maintain a neutral point of view throughout the article.
        """,
        messages=[
            {"role": "user", "content": f"Generate a Wikipedia-style page on {topic}."}
        ]
    )
    # print(message)
    x = message.model_dump(include={"content":True})
    changed = make_words_links(x["content"][0]["text"])
    print(changed)
    return render_template("generate2.html", topic=topic, generated_content=changed)

def make_words_links(html_text):
    words = html_text.split(" ")
    generated_html_text_with_links = ""
    for word in words:
        if len(word)>0 and word[0] == "<":
            generated_html_text_with_links+=word+" "
            continue
        if "<" in word or ">" in word:
            generated_html_text_with_links+=word+" "
            continue
        if not random.randint(0,3):
            generated_html_text_with_links+=word+" "
            continue
        if word == "/n":
            generated_html_text_with_links+="/n"
        elif len(word) > 5:
            generated_html_text_with_links+= f"""<a href="{LINK}{word}" style="text-decoration:none; color:black">""" + word + "</a>" 
            generated_html_text_with_links+=" "
        else:
            generated_html_text_with_links+=word+" "
    return generated_html_text_with_links

if __name__ == "__main__":
    app.run(debug=True, port=9999)