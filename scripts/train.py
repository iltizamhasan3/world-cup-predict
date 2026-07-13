"""CLI kecil untuk menjalankan pipeline yang sama dengan notebook."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training import run_training


if __name__ == "__main__":
    predictions, evaluation = run_training()
    print(
        f"Selesai: {len(predictions['matches'])} semifinal, "
        f"model skor {evaluation['score']['selected_model']}."
    )
