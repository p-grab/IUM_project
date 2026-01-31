## Aspect-Based Sentiment Analysis for Accommodation Reviews

This project creates ML automated system for analyzing large-scale accommodation reviews to identify which aspects of a stay (e.g., location, host) are most frequently praised or criticized by guests.

There are base model TF-IDF + K-Means + VADER sentiment and an advanced multilingual model using sentence embeddings and transformer-based sentiment analysis. The models operate on sentence-level data, group sentences into semantic aspects, classify their sentiment, and aggregate results per listing.

Also a a Flask-based microservice was implemented to show predictions through a simple API and supports A/B testing between the two models using transparent, deterministic assignment. The service returns top "k" positive and negative aspects for each listing and logs interactions for later evaluation.

Link to this project with datasets and models (.csv):
https://wutwaw-my.sharepoint.com/:u:/g/personal/01149927_pw_edu_pl/IQA_PlQ8fX5vS4jKin8y1rAMAUHnE_p75sgSxrngnE4rCV4?e=8ZdH94