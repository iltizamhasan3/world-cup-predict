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

Perintah training notebook dan dashboard akan tersedia setelah fase modeling selesai.

