# bookworm
 
CLI qui télécharge des livres depuis Project Gutenberg et en extrait des
infos : diversité lexicale, topics, entités nommées, résumé, livres
similaires.
 
## Lancer le projet
 
1. Installer Python et les paquets nécessaires
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```
 
2. Créer et activer l'environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```
 
3. Installer les dépendances
```bash
pip install -r requirements.txt
```
 
4. Lancer une commande
```bash
python3 bookworm.py --card 11
```
 
Au premier lancement, NLTK télécharge automatiquement les ressources
dont il a besoin (tokenizer, stopwords, etc), aucune étape manuelle.
 
## Usage
 
```
python3 bookworm.py --lexdiv <ID>      # diversité lexicale
python3 bookworm.py --topics <ID>      # topics par section
python3 bookworm.py --entities <ID>    # personnages / lieux
python3 bookworm.py --summarize <ID>   # résumé
python3 bookworm.py --similar <ID>     # 5 livres proches
python3 bookworm.py --card <ID>        # tout combiné
```
 
`<ID>` = id Gutenberg (ex : 11 = Alice au pays des merveilles). Une
seule option à la fois. Id invalide ou réseau down → message d'erreur
clair, pas de crash.
 
## Structure
 
```
bookworm.py
modules/
  downloader.py     téléchargement + cache (API Gutendex)
  text_utils.py     clean / tokenize / lemmatize / split en sections
  lexdiv.py
  entities.py
  topics.py
  summarize.py
  similar.py
  card.py           regroupe tout
diagrams/           un diagramme par tâche
requirements.txt
```
 
## Cache
 
Les livres téléchargés (`books/`) et les résultats calculés (`cache/`)
sont exclus du repo via `.gitignore`. Supprimables sans risque, tout
se retélécharge/recalcule automatiquement au prochain lancement.
 
## Organisation Git
 
Une branche par tâche (`feature_lexdiv`, `feature_entities`, etc.),
mergée dans `dev`, puis `dev` mergé dans `main` une fois le cœur du
projet stable et testé.
 
Convention de commits : `<type>(<scope>): <description>` —
`feat`, `docs`, `chore`.
 
## Notes techniques
 
- **lexdiv** : pas de lemmatisation, on veut le vrai vocabulaire de
  l'auteur, pas sa forme normalisée.
- **topics** : sections = chapitres (regex CHAPTER/PART). LDA, max 8
  topics même s'il y a plus de chapitres.
- **entities** : NER phrase par phrase. Charger le chunker NLTK une
  seule fois et le réutiliser (pas `ne_chunk()` direct à chaque appel)
  — sinon un livre entier passe de ~7s à ~13min.
- **summarize** : TextRank (`sumy`), extractif.
- **similar** : collection fixe de 21 livres (celle du sujet), TF-IDF
  + cosinus.
  
## Limites connues
 
- NER pas hyper précis (modèle statistique léger, pas deep learning)
- `--similar` marche seulement sur les 21 livres de la collection fixe
- optimisé pour l'anglais, autres langues moins fiables

## Diagrammes
 
### lexdiv
 
```mermaid
flowchart TD
    A[book_id] --> B[downloader.get_book_text\ndownload / read from books cache]
    A --> C[downloader.get_book_language]
    B --> D[text_utils.clean_text\nstrip PG header/footer, collapse spaces]
    D --> E[text_utils.tokenize_text\nword_tokenize, drop punctuation\nno stopword removal, no lemmatization]
    C --> E
    E --> F[Filter out pure-numeric tokens]
    F --> G[Count with collections.Counter]
    G --> H["Compute tok, typ, hap, ttr, mwl, mwf"]
    H --> I[Cache to cache/id_lexdiv.json]
    I --> J[Return dict]
```
 
### topics
 
```mermaid
flowchart TD
    A[book_id] --> B[downloader.get_book_text]
    A --> C[downloader.get_book_language]
    B --> D[text_utils.clean_text]
    D --> E[text_utils.split_sections\nsplit on CHAPTER/PART markers]
    E --> F[Per section: tokenize + remove stopwords\n+ lemmatize + drop narrative filler words]
    C --> F
    F --> G[Drop sections shorter than\nMIN_TOKENS_PER_SECTION]
    G --> H[gensim.corpora.Dictionary\n+ filter_extremes]
    H --> I[Build bag-of-words corpus]
    I --> J["LdaModel(num_topics = min(MAX_TOPICS, sections))"]
    J --> K[For each section: get its\nhighest-weight main topic]
    K --> L[Take top 10 words of that topic]
    L --> M[Cache to cache/id_topics.json]
    M --> N["Return {1: [...10 words], 2: [...], ...}"]
```
 
### entities
 
```mermaid
flowchart TD
    A[book_id] --> B[downloader.get_book_text]
    A --> C[downloader.get_book_language]
    B --> D["text_utils.clean_text(lower=False)\nkeep casing: capitals signal names"]
    D --> E[text_utils.split_sentences]
    E --> F[Per sentence: word_tokenize + pos_tag]
    F --> G["ne_chunker().parse(tagged)\nchunker instance loaded ONCE and reused"]
    G --> H["Keep PERSON chunks -> characters\nKeep GPE / LOCATION chunks -> locations"]
    H --> I[Drop false positives\nmr/mrs/gutenberg/chapter/...]
    I --> J[Merge case variants,\nkeep entities mentioned >= 2 times]
    J --> K[Cache to cache/id_entities.json]
    K --> L["Return {characters: [...], locations: [...]}"]
```
 
### summarize
 
```mermaid
flowchart TD
    A[book_id] --> B[downloader.get_book_text]
    A --> C[downloader.get_book_language]
    B --> D["text_utils.clean_text(lower=False)"]
    D --> E["sumy PlaintextParser + Tokenizer(language)"]
    C --> E
    E --> F[TextRankSummarizer\ngraph of sentences, edge = similarity]
    F --> G[Rank sentences like PageRank]
    G --> H[Keep top SUMMARY_SENTENCES\nin their original order]
    H --> I[Join into a single string]
    I --> J[Cache to cache/id_summarize.json]
    J --> K[Return summary string]
```
 
### similar
 
```mermaid
flowchart TD
    A[book_id] --> B{book_id in\nfixed 21-book COLLECTION?}
    B -- no --> Z[Error: not in reference collection]
    B -- yes --> C[Load / build cache/similar_corpus.json\ndownload + clean + lemmatize\nevery collection book, once]
    C --> D["TfidfVectorizer(unigrams+bigrams,\nsublinear_tf, min_df=2)"]
    D --> E[Fit-transform all 21 texts]
    E --> F["cosine_similarity(target, all)"]
    F --> G[Sort other 20 books\nby decreasing similarity]
    G --> H[Take top 5 -> map id to title]
    H --> I[Cache to cache/id_similar.json]
    I --> J["Return [title1, ..., title5]"]
```
 
### card
 
```mermaid
flowchart TD
    A[book_id] --> B[downloader.get_book_info]
    A --> C[lexdiv.get_lexdiv]
    A --> D[topics.get_topics]
    A --> E[entities.get_entities]
    A --> F[summarize.get_summarize]
    A --> G[similar.get_similar]
    B --> H[Assemble book card]
    C --> H
    D --> H
    E --> H
    F --> H
    G --> H
    H --> I["Return {info, lexdiv, topics,\nentities, summary, similar}"]
```
 