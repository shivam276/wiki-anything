from flask import Flask, render_template, request
import anthropic
app = Flask(__name__)

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
        max_tokens=500,
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
    print(x["content"])
    return x["content"][0]["text"]
if __name__ == "__main__":
    app.run(debug=True, port=9999)