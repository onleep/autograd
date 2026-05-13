import pandas as pd
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('cointegrated/rubert-tiny2')


def embedding(data: pd.Series) -> pd.Series:
    embeds = model.encode(
        data['description'],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeds = pd.Series(embeds, index=[f'desc_{i}' for i in range(embeds.shape[0])])
    return pd.concat([data.drop(labels=['description']), embeds])
