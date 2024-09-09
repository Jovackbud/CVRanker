'''
Imports
'''
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

'''
scrape CVs and JD into an iterable
'''
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text


'''
set up gemini flask api and instantiate model
'''


'''
Summarize Skills and Experiences using gemini and store in an iterable
'''

'''
vectorize the summary and train a  machine learning model, preferably Kmeans on the JD
'''
def vectorizer(cv_texts, jdtext):
    # Vectorize the texts
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(cv_texts + [jd_text])
    return X


'''
train a  machine learning model, preferably Kmeans on the JD
'''
def training(X):
    # Apply K-Means clustering
    kmeans = KMeans(n_clusters=2, random_state=42).fit(X)
    return kmeans

'''
pass summary and name into a k mean of JD and classify
'''
def prediction(kmeans, X):
    # Find the cluster of the JD
    jd_cluster = kmeans.predict(X[-1])
    # Rank CVs based on their distance to the JD cluster
    distances = cosine_similarity(X[:-1], X[-1])
    ranked_cvs = sorted(zip(cv_texts, distances), key=lambda x: x[1], reverse=True)
    return jd_cluster, distances, ranked_cvs

'''
return name, summary and kmeans predictions as a tuple and/or data frame
'''

