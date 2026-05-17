from pathlib import Path

from sentence_transformers import SentenceTransformer

MODEL_NAME = "keepitreal/vietnamese-sbert"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "vietnamese-sbert"


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Download and save the model locally so the server can load it from disk.
    model = SentenceTransformer(MODEL_NAME)
    model.save(str(MODEL_DIR))

    print(f"Saved model to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
