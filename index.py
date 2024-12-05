import os
import unicodedata
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import pdfplumber

# Télécharger les ressources nécessaires pour NLTK
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Initialisation de la base de données SQLAlchemy
Base = declarative_base()
engine = create_engine('sqlite:///inverted_index.db')
Session = sessionmaker(bind=engine)

# Initialisation de SpaCy avec le modèle français pour la lemmatisation
nlp = spacy.load('fr_core_news_sm')

# Définition des classes pour la base de données (Documents, Termes et Postings)
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)

class Term(Base):
    __tablename__ = 'terms'
    id = Column(Integer, primary_key=True)
    term = Column(String, unique=True)
    postings = relationship('Posting', back_populates='term')

class Posting(Base):
    __tablename__ = 'postings'
    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey('terms.id'))
    document_id = Column(Integer, ForeignKey('documents.id'))
    frequency = Column(Integer)  # Fréquence du terme dans le document
    positions = Column(String)  # Positions dans le document
    
    # Relations pour accéder aux documents et termes associés
    term = relationship('Term', back_populates='postings')
    document = relationship('Document', back_populates='postings')

Document.postings = relationship('Posting', back_populates='document')

# Création des tables dans la base de données
Base.metadata.create_all(engine)

# Normalisation et lemmatisation du texte en français
def normalize_text(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    tokens = word_tokenize(text, language='french')
    stop_words = set(stopwords.words('french'))
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
    
    # Lemmatisation avec Spacy
    doc = nlp(" ".join(tokens))
    lemmas = [token.lemma_ for token in doc]
    
    return lemmas

# Extraction du texte d'un fichier PDF avec PyPDF2
def extract_pdf_text(pdf_path):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte de {pdf_path}: {e}")
        return ""

# Fonction d'indexation des documents PDF dans un dossier
def index_documents(folder_path):
    session = Session()
    try:
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(folder_path, filename)
                
                # Vérifier si le document est déjà indexé
                existing_document = session.query(Document).filter_by(filename=filename).first()
                if existing_document:
                    print(f"{filename} est déjà indexé, passage au suivant.")
                    continue  # Passer au fichier suivant si déjà indexé

                text = extract_pdf_text(pdf_path)
                if not text:
                    print(f"Impossible d'extraire du texte de {filename}, passage au suivant.")
                    continue
                
                tokens = normalize_text(text)
                
                # Ajout du document
                document = Document(filename=filename)
                session.add(document)
                session.flush()  # Assurer l'ajout du document avant de continuer
                
                term_data = {}
                for pos, term in enumerate(tokens):
                    if term not in term_data:
                        term_data[term] = {"frequency": 0, "positions": []}
                    term_data[term]["frequency"] += 1
                    term_data[term]["positions"].append(pos)
                
                for term, data in term_data.items():
                    term_entry = session.query(Term).filter_by(term=term).first()
                    if not term_entry:
                        term_entry = Term(term=term)
                        session.add(term_entry)
                        session.flush()
                    
                    posting = Posting(
                        term_id=term_entry.id,
                        document_id=document.id,
                        frequency=data["frequency"],
                        positions=",".join(map(str, data["positions"]))
                    )
                    session.add(posting)
                
        session.commit()
        print("Indexation terminée.")
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de l'indexation : {e}")
    finally:
        session.close()
