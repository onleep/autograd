import pandas as pd
from sentence_transformers import SentenceTransformer


def embedding(data: pd.DataFrame) -> pd.DataFrame:
    model = SentenceTransformer('cointegrated/rubert-tiny2')
    texts = data['description'].fillna('').tolist()
    embeds = model.encode(
        texts,
        batch_size=16,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    embeds = pd.DataFrame(
        embeds,
        index=data.index,
        columns=[f'desc_{i}' for i in range(embeds.shape[1])],
    )
    return pd.concat([data.drop(columns=['description']), embeds], axis=1)
