# autograd

> 🏎️ Full-cycle platform for car price prediction on the Russian market

## 🎯 Aim of the project

The project automates the entire pipeline: offer collection, offer data storage, dataset preparation, model training, ML artifact publishing, and prediction delivery through an API and web interface.

## 🧩 Architecture

| Module         | Purpose                                                                         | What it stores / returns                                                             |
| -------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `parser`       | Collects car sale offer data, descriptions, and photos                          | `MySQL` tables `Offers`, `Attributes`, `Specifications`, `Photos`; photos in `MinIO` |
| `ml`           | Prepares the training dataset, aggregates, and trains the model                 | `train_df.parquet`, `aggs_df.parquet`, `mlb_*.pkl`, `model_*.cbm` in `MinIO`         |
| `api`          | Loads the model and artifacts from `MinIO`, creates the prediction endpoint     | `POST /predict`                                                                      |
| `frontend`     | Streamlit application for entering car parameters and comparing with the market | UI for price estimation                                                              |
| Infrastructure | `MySQL`, `MinIO`, `Grafana`, `phpMyAdmin`, `vLLM`, `Caddy`                              | Storage, administration and reverse proxy                                            |

Data flow: `parser -> MySQL / MinIO -> ml -> MinIO -> api -> frontend`.

## 🔍 Module details

### `parser`

Schedule:

- 🕛 `00:00` — offer collection / update;
- 🕛 `12:00` — saving photos to S3 MinIO.

### `ml`

- encoding multi-value features and saving encoders;
- training `CatBoostRegressor`;
- saving the model to `MinIO`.
  > Training can be started if there are more than `100_000` offers in MySQL

## 🗂️ Storing Data

### `MySQL`

- `Offers` — basic offer information;
- `Attributes` — description, region, owners, VIN attributes, tags;
- `Specifications` — car technical specifications;
- `Photos` — image links and status.

### `MinIO` bucket `main`

- `data/train_df.parquet` — training dataset;
- `data/aggs_df.parquet` — aggregates for the API;
- `data/mlb_tags.pkl`, `data/mlb_equip.pkl` — encoders;
- `data/model_*.cbm` — trained models;
- `<autoru_id>/*.jpg` — car photos.

## 🚀 Launch

### 0. You can use either a domain or your machine's IP.

- To use a domain, set the `DOMAIN=<your.domain>` variable in `.env`
- To use services without a domain, expose ports in the docker-compose containers. Grafana - 3000, phpMyAdmin - 80, MinIO - 9001, frontend - 8501. Example:

```
phpmyadmin:
  image: phpmyadmin:5.2.3
  ports:
    - <target_port>:80
```

### 1. Prepare env

`.env.dev` in the project serves as a template. Before building, create a working `.env`:

```bash
cp .env.dev .env
```

After that, fill in the values in `.env`.

### 2. Start containers

```bash
docker compose up -d --build
```

### 3. Create the `main` bucket in MinIO once

This step only needs to be done on the first launch.

- 🔐 log in using `S3_ID` / `S3_KEY`;
- 📦 create a bucket named `main`.

MinIO Console address: `https://cdn.<DOMAIN>`;

## 🔗 Access points

- `https://<DOMAIN>` — frontend;
- `https://graf.<DOMAIN>` — Grafana;
- `https://pma.<DOMAIN>` — phpMyAdmin;
- `https://cdn.<DOMAIN>` — MinIO Console;
