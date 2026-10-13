# Backend_emotune

Django REST backend for EmoTune: emotion classification (fine-tuned BERT with a
GoEmotions fallback) and therapist-validated music recommendations via Spotify.

## Deploying on a server (e.g. AWS EC2)

Needs a machine with at least 4 GB RAM (the models take ~1.5 GB), Docker, and
a domain name pointing at it (Caddy uses it for the HTTPS certificate).

```bash
git clone https://github.com/John-Vincent-Urie/Backend_emotune.git
cd Backend_emotune

# The trained model is a release asset, not part of git (private repo:
# export GH_TOKEN=<token with read access> first).
gh release download model-2026-09-28 -R John-Vincent-Urie/Backend_emotune
sha256sum -c bert_emotion_model.tar.gz.sha256
tar -xzf bert_emotion_model.tar.gz -C ml/models/

cp .env.prod.example .env      # fill in DOMAIN, secrets, Spotify, email
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

The admin is then at `https://<DOMAIN>/django-admin/`. Point the app at it by
building the APK with `--dart-define=API_BASE_URL=https://<DOMAIN>/api`.
