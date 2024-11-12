

# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')  # Cela doit correspondre au fichier 'index.html' dans le dossier 'templates'

# if __name__ == '__main__':
#     app.run(debug=True)
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    results = search_documents(query)
    return render_template('index.html', query=query, results=results)

def search_documents(query):
    # Simulation de recherche dans une base de données ou un ensemble de documents
    documents = [
        {'title': 'Introduction à Python', 'url': 'http://example.com/python', 'description': 'Apprenez les bases de Python.'},
        {'title': 'Big Data et Hadoop', 'url': 'http://example.com/hadoop', 'description': 'Tout savoir sur Hadoop et le Big Data.'},
        {'title': 'Machine Learning', 'url': 'http://example.com/ml', 'description': 'Une introduction au machine learning.'},
        {'title': 'Développement Web avec Flask', 'url': 'http://example.com/flask', 'description': 'Créez des applications web avec Flask.'},
        # Ajoutez d'autres documents ici...
    ]
    return [doc for doc in documents if query.lower() in doc['title'].lower()]

from indexer import index_documents

documents_folder = "documents"
index_documents(documents_folder)
print("Indexation terminée !")

if __name__ == '__main__':
    app.run(debug=True)

