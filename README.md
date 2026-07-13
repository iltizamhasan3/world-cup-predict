# World Cup Predict

Pipeline probabilistik dan dashboard lokal berbahasa Indonesia untuk menganalisis semifinal Piala Dunia 2026:

- France vs Spain
- England vs Argentina

Versi pertama memodelkan skor 90 menit, hasil home/draw/away, peluang lolos, peluang adu penalti, serta distribusi statistik pertandingan. Dashboard juga menyediakan ringkasan 48 tim dan 1.248 pemain.

## Menyiapkan lingkungan

Proyek menggunakan Python 3.13.4.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Raw CSV tidak disertakan di repository. Letakkan sumber data lokal di folder `data/` dengan nama file yang dijelaskan oleh pipeline. Model binary juga tetap lokal; artifact JSON hasil evaluasi dan prediksi dapat dilacak Git.

## Menjalankan

Jalankan training melalui notebook `notebooks/01_training.ipynb`, atau gunakan CLI
yang memanggil pipeline identik:

```bash
.venv/bin/python scripts/train.py
```

Hasil yang aman dipublikasikan ditulis ke `artifacts/predictions.json`,
`artifacts/evaluation.json`, dan `artifacts/metrics_summary.csv`. Model binary tetap
berada di `artifacts/models/` dan diabaikan Git.

Jalankan dashboard lokal setelah artifact tersedia:

```bash
.venv/bin/streamlit run app.py
```

Halaman Prediksi dan Evaluasi dapat dibuka hanya dengan artifact repository.
Halaman Tim dan Pemain memerlukan raw CSV lokal di folder `data/`.
