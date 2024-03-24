from flask import Flask, render_template, request

from vector_search import VectorSearch

vector = VectorSearch()
app = Flask(__name__, template_folder="src/templates")


@app.route('/', methods=['GET'])
def index():
    return render_template('search.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    # Perform search logic here
    results = vector.search(query)[:10]
    return render_template('search.html', results=results, query=query)
