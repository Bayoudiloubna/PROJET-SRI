
import os
import unicodedata
import PyPDF2
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from lemminflect import getLemma
import nltk

# Télécharger les ressources NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('french_lefff')

# Initialisation de la base de données
Base = declarative_base()
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

# Tables de la base de données
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)

class Term(Base):
    __tablename__ = 'terms'
    id = Column(Integer, primary_key=True)
    term = Column(String, unique=True)

class Posting(Base):
    __tablename__ = 'postings'
    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey('terms.id'))
    document_id = Column(Integer, ForeignKey('documents.id'))
    positions = Column(String)
    term = relationship("Term")
    document = relationship("Document")

Base.metadata.create_all(engine)

# Nettoyage et Normalisation
def normalize_text(text):
    text = text.lower()
    # Supprimer les accents
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    
    # Tokenisation et filtrage
    tokens = word_tokenize(text, language='french')
    stop_words = set(stopwords.words('french'))

    # Lemmatization avec french_lefff
    lemmatized_tokens = []
    for word in tokens:
        if word.isalpha() and word not in stop_words:
            lemma = getLemma(word, upos='NOUN')  # Pour les noms, utilisez 'VERB' pour les verbes, etc.
            lemmatized_tokens.append(lemma[0] if lemma else word)
    
    return lemmatized_tokens

# Extraction de texte à partir d'un PDF
def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Fonction d'indexation des documents
def index_documents(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            text = extract_pdf_text(pdf_path)
            tokens = normalize_text(text)

            # Ajouter le document à la base de données
            doc_entry = Document(filename=filename)
            session.add(doc_entry)
            session.commit()

            # Calculer les positions des termes
            term_positions = defaultdict(list)
            for pos, term in enumerate(tokens):
                term_positions[term].append(pos)

            # Ajouter chaque terme et ses positions dans la base de données
            for term, positions in term_positions.items():
                term_entry = session.query(Term).filter_by(term=term).first()
                if not term_entry:
                    term_entry = Term(term=term)
                    session.add(term_entry)
                    session.commit()

                # Ajouter le posting avec les positions
                posting = Posting(
                    term_id=term_entry.id,
                    document_id=doc_entry.id,
                    positions=",".join(map(str, positions))
                )
                session.add(posting)

            session.commit()
