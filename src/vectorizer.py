from typing import List, Optional

from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel


def embed_text(
    texts: list = None,
    task: str = "SEMANTIC_SIMILARITY",
) -> List[List[float]]:
    """Embeds texts with a pre-trained, foundational model.
    Args:
        texts (List[str]): A list of texts to be embedded.
        task (str): The task type for embedding. Check the available tasks in the model's documentation.
        dimensionality (Optional[int]): The dimensionality of the output embeddings.
    Returns:
        List[List[float]]: A list of lists containing the embedding vectors for each input text
    """
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    embeddings = model.get_embeddings(inputs)
    # Example response:
    # [[0.006135190837085247, -0.01462465338408947, 0.004978656303137541, ...],
    return [embedding.values for embedding in embeddings]
