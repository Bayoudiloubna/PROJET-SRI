from flask import Flask, render_template, request, send_file, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import threading
from index import index_documents  # Fonction d'indexation
from search import search_documents  # Fonction de recherche
from file_watcher import start_watching  # Import de la fonction de surveillance

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données
DATABASE_URL = "sqlite:///inverted_index.db"  
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Chemin vers le dossier des documents
DOCUMENTS_FOLDER = "documents"

@app.route('/')
def index():
    """
    Page d'accueil de l'application.
    """
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def result():
    """
    Route pour traiter une requête de recherche et retourner les résultats.
    """
    query = request.form.get('query', '').strip()  # Récupérer la requête
    if not query:
        return render_template('result.html', results=[], error="La requête est vide.")

    with Session() as session:
        try:
            # Recherche des documents pertinents
            results = search_documents(query, session)
            return render_template('result.html', results=results)
        except Exception as e:
            return render_template('result.html', results=[], error=f"Erreur lors de la recherche : {e}")


@app.route('/download/<filename>')
def download_file(filename):
    """
    Route pour télécharger un fichier depuis le dossier des documents.
    """
    file_path = os.path.join(DOCUMENTS_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404, description="Fichier introuvable.")  # Renvoie une erreur 404


if __name__ == '__main__':
    print("Indexation des documents en cours...")
    # Indexation des documents présents dans le dossier au démarrage
    index_documents(DOCUMENTS_FOLDER)
    print("Indexation terminée.")

    # Démarrer la surveillance des fichiers dans un thread séparé
    file_watcher_thread = threading.Thread(target=start_watching, daemon=True)
    file_watcher_thread.start()

    print("Démarrage du serveur Flask...")
    app.run(debug=True)
