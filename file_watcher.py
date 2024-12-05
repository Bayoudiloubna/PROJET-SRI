import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from index import index_documents
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from index import Document, Posting, Term

# Dossier à surveiller
DOCUMENTS_FOLDER = "documents"

# Configuration de la base de données
DATABASE_URL = "sqlite:///inverted_index.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def remove_document_from_index(file_path):
    """
    Supprime un document, ses postings associés, et les termes orphelins de l'index.
    """
    session = Session()
    try:
        filename = os.path.basename(file_path)
        # Recherche du document
        document = session.query(Document).filter_by(filename=filename).first()
        if document:
            # Récupérer les IDs des termes avant suppression des postings
            term_ids = session.query(Posting.term_id).filter_by(document_id=document.id).all()

            # Suppression des postings associés au document
            session.query(Posting).filter_by(document_id=document.id).delete()

            # Suppression du document lui-même
            session.delete(document)
            session.commit()
            print(f"Document {filename} supprimé de l'index.")

            # Vérification et suppression des termes orphelins
            for term_id in term_ids:
                if not session.query(Posting).filter_by(term_id=term_id[0]).first():
                    session.query(Term).filter_by(id=term_id[0]).delete()
                    print(f"Terme orphelin supprimé : ID {term_id[0]}")

            session.commit()
        else:
            print(f"Aucun document trouvé pour {filename} dans l'index.")
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la suppression de {file_path} : {e}")
    finally:
        session.close()



class WatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        """
        Lorsque de nouveaux fichiers sont ajoutés au dossier, cette méthode est appelée.
        """
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            print(f"Nouvel fichier détecté : {event.src_path}")
            # Indexation du fichier PDF ajouté
            index_documents(os.path.dirname(event.src_path))

    def on_deleted(self, event):
        """
        Lorsque des fichiers sont supprimés du dossier, cette méthode est appelée.
        """
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            print(f"Fichier supprimé détecté : {event.src_path}")
            # Suppression du fichier de l'index
            remove_document_from_index(event.src_path)

def start_watching():
    """
    Fonction pour démarrer la surveillance du dossier.
    """
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, DOCUMENTS_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    print("Démarrage de la surveillance du dossier...")
    start_watching()
