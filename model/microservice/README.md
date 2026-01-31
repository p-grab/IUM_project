Flask API z A/B dla modelu analizy aspektów najbardziej i najmniej chwalonych



## Instalacja i uruchomienie:

pip install -r requirements.txt
cd microservice
python app.py

Serwis działa na `http://localhost:8080`

## Komendy 

Predykcja aspektów:
curl.exe -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d '{\"listing_id\": 10719987, \"top_k\": 3}'

Timeline (wykres w przeglądarce):

http://localhost:8080/predict/chart?listing_id=10719987
http://localhost:8080/predict/LINK
LINK jest otrzymywany w odpowiedzi curl

Tworzenie danych do eksperymentu A/B:
cd microservice
generate_ab_data.py

Logi w `ab_log.csv`