import math
from collections import defaultdict
from sqlalchemy.orm import sessionmaker
from index import Posting, Document, Term, Session, normalize_text

# Calcul du score TF-IDF pour un terme dans un document
def calculate_tf_idf(session, term, document_id, total_docs):
    try:
        posting = session.query(Posting).filter_by(term_id=term.id, document_id=document_id).first()
        if not posting:
            return 0  # Si le terme n'existe pas dans ce document, retourner 0
        term_frequency = posting.frequency
        document_frequency = len(term.postings) if term.postings else 1  # Éviter division par 0
        idf = math.log(total_docs / (1 + document_frequency))
        return term_frequency * idf
    except Exception as e:
        print(f"Erreur dans le calcul TF-IDF pour le terme {term.term}: {e}")
        return 0


# Construction des vecteurs TF-IDF pour tous les documents
def build_document_vectors(session):
    terms = session.query(Term).all()  # Récupère tous les termes
    total_docs = session.query(Document).count()  # Nombre total de documents
    document_vectors = defaultdict(lambda: defaultdict(float))  # Dictionnaire pour stocker les vecteurs
    
    for term in terms:
        for posting in term.postings:
            tf_idf = calculate_tf_idf(session, term, posting.document_id, total_docs)
            document_vectors[posting.document_id][term.term] = tf_idf  # Enregistrer le score TF-IDF pour chaque document
    
    return document_vectors

# Construction du vecteur TF-IDF pour la requête
def build_query_vector(query, session, total_docs):
    tokens = normalize_text(query)  # Normalisation et tokenisation de la requête
    query_vector = defaultdict(float)  # Dictionnaire pour stocker les scores TF-IDF de la requête
    
    for token in tokens:
        term = session.query(Term).filter_by(term=token).first()  # Recherche du terme dans la base
        if term:
            document_frequency = len(term.postings)  # Calcul de la fréquence des documents contenant le terme
            idf = math.log(total_docs / (1 + document_frequency))  # Calcul de l'IDF
            query_vector[token] += idf  # Ajouter l'IDF au vecteur de la requête

    return query_vector

# Calcul de la similarité cosinus entre deux vecteurs
def cosine_similarity(vector1, vector2):
    dot_product = sum(vector1[term] * vector2.get(term, 0) for term in vector1)  # Produit scalaire
    magnitude1 = math.sqrt(sum(value ** 2 for value in vector1.values()))  # Norme du vecteur 1
    magnitude2 = math.sqrt(sum(value ** 2 for value in vector2.values()))  # Norme du vecteur 2
    
    if magnitude1 == 0 or magnitude2 == 0:  # Si l'un des vecteurs est nul, la similarité est 0
        return 0.0
    return dot_product / (magnitude1 * magnitude2)  # Retourner la similarité cosinus

# Fonction de recherche des documents pertinents pour une requête
# Fonction de recherche des documents pertinents pour une requête
def search_documents(query, session):
    total_docs = session.query(Document).count()  # Nombre total de documents
    document_vectors = build_document_vectors(session)  # Vecteurs TF-IDF pour les documents
    query_vector = build_query_vector(query, session, total_docs)  # Vecteur TF-IDF pour la requête

    scores = {}

    for doc_id, doc_vector in document_vectors.items():
        similarity = cosine_similarity(query_vector, doc_vector)
        if similarity > 0:
            scores[doc_id] = similarity

    # Trier les documents par pertinence
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Récupérer les 5 documents les plus pertinents, sans le score
    top_documents = []
    for doc_id, score in sorted_scores[:6]:  # Limité à 6 documents
        document = session.query(Document).filter_by(id=doc_id).first()
        if document:
            top_documents.append({'filename': document.filename})  # Suppression du score

    return top_documents
