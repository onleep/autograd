import pandas as pd


def build_aggregates(data: pd.DataFrame) -> pd.DataFrame:
    columns = ['price', 'photos_name', 'predicted_prices', 'autoru_id', 'description']
    data = data.drop(columns=columns)
    cat_cols = data.select_dtypes(include='object').columns.to_list()
    levels = [
        ['mark', 'model', 'year'],
        ['mark', 'model', 'year', 'trim'],
        ['mark', 'model', 'year', 'generation'],
        ['mark', 'model', 'year', 'generation', 'trim'],
    ]
    result: list[pd.DataFrame] = []
    for group in levels:
        num_cols = [
            col for col in data.columns if col not in cat_cols and col not in group
        ]
        t_cat_cols = [col for col in cat_cols if col not in group]
        num = data.groupby(group, dropna=False)[num_cols].mean().reset_index()
        cat = (
            data.groupby(group, dropna=False)[t_cat_cols]
            .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else '')
            .reset_index()
        )
        agg = num.merge(cat, on=group)
        agg['group'] = str(group)
        result.append(agg)
    return pd.concat(result, ignore_index=True)
