import numpy as np
import pandas as pd

from clients.database import Specifications


def prepare_df(column: pd.Series) -> pd.DataFrame:
    keys = set(k for d in column.dropna() for k in d)
    extract_values = lambda x: (
        {k: x[k]['value'] for k in keys if k in x} if isinstance(x, dict) else {}
    )
    to_number = lambda v: (
        float(v) if isinstance(v, str) and v.replace('.', '', 1).isdigit() else v
    )
    return column.dropna().apply(extract_values).apply(pd.Series).map(to_number)


async def prepare_specs() -> pd.DataFrame:
    df_specs = pd.DataFrame(await Specifications.all().values())
    drop_columns = ['id', 'created_at', 'updated_at']
    df_specs.drop(columns=drop_columns, inplace=True)
    # base
    df_values = prepare_df(df_specs['base'])
    df_values.drop(columns=['total_range'], inplace=True)
    df_values = df_values.add_prefix('base_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['base'], inplace=True)
    # general
    df_values = prepare_df(df_specs['general'])
    df_values['seats'] = df_values['seats'].map(
        lambda v: np.mean(list(map(float, v.split(', ')))) if isinstance(v, str) else v
    )
    df_values = df_values.add_prefix('general_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['general'], inplace=True)
    # sizes
    df_values = prepare_df(df_specs['sizes'])
    df_values['clearance'] = df_values['clearance'].map(
        lambda v: np.mean(list(map(float, v.split('-')))) if isinstance(v, str) else v
    )
    parts = (
        df_values['disk_size']
        .dropna()
        .map(lambda v: v.replace('ET-', '').replace('ET', '').replace(',', '').split())
    )
    ## 1x1 size (6.5x16 50, 6x15 46)
    xsize0 = parts.map(
        lambda x: [float(p.lower().split('x')[0]) for p in x if 'x' in p.lower()]
    )
    xsize1 = parts.map(
        lambda x: [float(p.lower().split('x')[1]) for p in x if 'x' in p.lower()]
    )
    df_values.loc[parts.index, 'disk_x0_min'] = xsize0.map(min)
    df_values.loc[parts.index, 'disk_x0_max'] = xsize0.map(max)
    df_values.loc[parts.index, 'disk_x1_min'] = xsize1.map(min)
    df_values.loc[parts.index, 'disk_x1_max'] = xsize1.map(max)
    ## ET
    et = parts.map(lambda x: [float(p) for p in x if p.replace('.', '', 1).isdigit()])
    df_values.loc[parts.index, 'disk_et_min'] = et.map(min)
    df_values.loc[parts.index, 'disk_et_max'] = et.map(max)
    df_values.drop(columns=['disk_size'], inplace=True)
    ## landing_wheels_size
    ### tswzise
    wzise = df_values['landing_wheels_size'].dropna()
    parts = wzise.str.split()
    dia = parts.map(lambda x: float(x[0].replace('DIA', '')))
    size = parts.map(lambda x: x[1].split('x'))
    df_values.loc[wzise.index, 'wheels_dia'] = dia
    df_values.loc[wzise.index, 'wheels_size_x0'] = size.map(lambda x: float(x[0]))
    df_values.loc[wzise.index, 'wheels_size_x1'] = size.map(lambda x: float(x[1]))
    df_values.drop(columns=['landing_wheels_size'], inplace=True)
    ### tsize
    tsize = df_values['origin_tires_size'].dropna()
    items = tsize.str.split(', ').explode()
    p = items.str.split(' ', expand=True)
    wh = p[0].str.split('/', expand=True).astype(float)
    rim = p[1].str.replace('R', '', regex=False).astype(float)
    agg = (
        pd.concat({'width': wh[0], 'profile': wh[1], 'rim': rim}, axis=1)
        .groupby(level=0)
        .agg(['min', 'max'])
    )
    agg.columns = [f'tires_{a}_{b}' for a, b in agg.columns]
    agg['tires_count'] = items.groupby(level=0).size().astype(float)
    df_values.loc[agg.index, agg.columns] = agg
    df_values.drop(columns=['origin_tires_size'], inplace=True)
    df_values = df_values.add_prefix('sizes_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['sizes'], inplace=True)
    # volume_and_mass
    df_values = prepare_df(df_specs['volume_and_mass'])
    bvolume = df_values['boot_volume'].dropna().astype(str).str.split('/', expand=True)
    df_values.loc[bvolume.index, 'boot'] = bvolume[0].astype(float)
    df_values.loc[bvolume.index, 'volume'] = bvolume[1].map(
        lambda x: float(x) if x else None
    )
    df_values.drop(columns=['boot_volume'], inplace=True)
    df_values = df_values.add_prefix('volume_and_mass_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['volume_and_mass'], inplace=True)
    # transmission
    df_values = prepare_df(df_specs['transmission'])
    df_values = df_values.add_prefix('transmission_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['transmission'], inplace=True)
    # suspension_and_brakes
    df_values = prepare_df(df_specs['suspension_and_brakes'])
    df_values = df_values.add_prefix('suspension_and_brakes_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['suspension_and_brakes'], inplace=True)
    # performance_indicators
    df_values = prepare_df(df_specs['performance_indicators'])
    ## emission_euro_class
    df_values['emission_euro_class'] = (
        df_values['emission_euro_class'].str.replace('Euro ', '').astype(float)
    )
    ## consumption
    parts = (
        df_values['consumption']
        .str.split('/', expand=True)
        .replace('-', np.nan)
        .astype(float)
    )
    df_values['consumption_city'] = parts[0]
    df_values['consumption_highway'] = parts[1]
    df_values['consumption_mixed'] = parts[2]
    df_values.drop(columns=['consumption'], inplace=True)
    df_values.drop(columns=['consumption_kwt'], inplace=True)
    df_values = df_values.add_prefix('performance_indicators_')
    df_specs = df_specs.join(df_values)
    df_specs.drop(columns=['performance_indicators'], inplace=True)
    # engine
    df_values = prepare_df(df_specs['engine'])
    df_values.drop(columns=['consumption_calc'], inplace=True)
    ## diameter
    parts = df_values['diameter'].str.split('x', expand=True)
    df_values['diameter_x0'] = parts[0].str.replace(',', '.', 1).astype(float)
    df_values['diameter_x1'] = parts[1].str.replace(',', '.', 1).astype(float)
    df_values.drop(columns=['diameter'], inplace=True)
    ## max_power
    df_values['max_power_hp'] = (
        df_values['max_power'].str.extract(r'(\d+)\s*л.с')[0].astype(float)
    )
    df_values['max_power_kw'] = (
        df_values['max_power'].str.extract(r'(\d+)\s*кВт')[0].astype(float)
    )
    df_values['max_power_rpm'] = (
        df_values['max_power'].str.extract(r'(\d+)\s*об')[0].astype(float)
    )
    df_values.drop(columns=['max_power_hp', 'max_power'], inplace=True)
    ## moment
    df_values['moment_nm'] = (
        df_values['moment'].str.extract(r'(\d+)\s*Н⋅м')[0].astype(float)
    )
    df_values['moment_rpm'] = (
        df_values['moment'].str.extract(r'(\d+)\s*об')[0].astype(float)
    )
    df_values.drop(columns=['moment'], inplace=True)
    df_values.drop(columns=['engine_id'], inplace=True)
    df_values = df_values.add_prefix('engine_')
    df_specs = df_specs.join(df_values)
    # final
    df_specs.drop(columns=['engine'], inplace=True)
    df_specs.drop(columns=['base_electric_range'], inplace=True)
    mask = df_specs['engine_engine_list'].apply(
        lambda x: isinstance(x, float) and not pd.isna(x)
    )
    df_specs.loc[mask, 'engine_engine_list'] = df_specs.loc[
        mask, 'engine_engine_list'
    ].astype(int)
    df_specs['engine_engine_list'] = df_specs['engine_engine_list'].astype(str)
    return df_specs
