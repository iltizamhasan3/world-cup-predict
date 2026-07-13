"""CLI kecil untuk menjalankan pipeline yang sama dengan notebook."""

from src.training import run_training


if __name__ == "__main__":
    predictions, evaluation = run_training()
    print(
        f"Selesai: {len(predictions['matches'])} semifinal, "
        f"model skor {evaluation['score']['selected_model']}."
    )

