import pandas as pd
from calendar import monthrange


def fix_columns_names(df: pd.DataFrame):

    try:
        nomes_coluna_1 = df.columns
        nomes_coluna_1 = [str(name) for name in df.columns]
        nomes_coluna_2 = [str(name) for name in df.iloc[0, :]]
        nomes_coluna = []

        for i, nome in enumerate(nomes_coluna_1):
            if nome.split(":")[0] == "Unnamed":
                nomes_coluna_1[i] = ""

        for i in range(len(nomes_coluna_1)):
            nome_coluna_junta = nomes_coluna_1[i].strip() + " " + nomes_coluna_2[i].strip()
            nome_coluna_junta = nome_coluna_junta.strip()
            nomes_coluna.append(nome_coluna_junta)

        df = df.iloc[1:, :]
        df.columns = nomes_coluna

    except:
        print("Error!!!")
        
    return df


def drop_nan_named_columns(df):
    """
    Remove colunas cujo nome seja a string 'nan' de um DataFrame.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame de onde as colunas com nome 'nan' serão removidas.

    Retorna:
    --------
    pd.DataFrame
        DataFrame sem colunas com nome 'nan'.
    """
    # Converter os nomes das colunas para string e remover aqueles que são "nan"
    df = df.loc[:, ~df.columns.astype(str).isin(["nan", "NaN", "None"])]
    
    return df


def clean_time_column(df):
    """
    Converte a coluna "Time" para o formato correto HH:00:00.
    
    Se a coluna "Time" estiver no formato '1900-01-01 HH:MM:SS',
    a função extrai apenas a hora e a converte para 'HH:00:00'.
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo a coluna "Time" com formato incorreto.

    Retorna:
    --------
    pd.DataFrame
        DataFrame com "Time" formatado corretamente.
    """
    
    # Converter para string e garantir que valores NaN sejam tratados
    df["Time"] = df["Time"].astype(str)

    # Extrair a hora do formato "1900-01-01 HH:MM:SS" ou qualquer formato estranho
    df["Time"] = df["Time"].apply(lambda x: f"{x[-8:-6]}:00:00" if len(x) >= 8 else x)

    return df


def standardize_dataframes(dfs):
    """
    Padroniza todos os DataFrames para possuírem as mesmas colunas,
    garantindo que "Date" e "Time" sejam as primeiras colunas,
    adicionando colunas ausentes com valores NaN e removendo colunas extras.

    Parâmetros:
    -----------
    dfs : dict
        Dicionário contendo vários DataFrames (chave = nome, valor = DataFrame).

    Retorna:
    --------
    dict
        Dicionário atualizado, onde todos os DataFrames possuem as mesmas colunas,
        com "Date" e "Time" no início.
    """

    # Passo 1: Coletar todas as colunas possíveis
    all_columns = set()
    for df in dfs.values():
        all_columns.update(df.columns)

    # Converter para lista ordenada para manter um padrão
    all_columns = sorted(all_columns)

    # Passo 2: Garante que "Date" e "Time" sejam as primeiras colunas, mantendo a ordem das demais
    column_order = ["Date", "Time"] + [col for col in all_columns if col not in ["Date", "Time"]]

    # Passo 3: Iterar sobre cada DataFrame para padronizar colunas
    for key, df in dfs.items():
        # Adicionar colunas ausentes com valores NaN
        missing_columns = set(all_columns) - set(df.columns)
        for col in missing_columns:
            df[col] = None

        # Remover colunas extras (se houver)
        extra_columns = set(df.columns) - set(all_columns)
        if extra_columns:
            df = df.drop(columns=extra_columns)

        # Reordenar as colunas para manter "Date" e "Time" no início
        dfs[key] = df[column_order]

    return dfs


def filter_valid_dates(df):
    """
    Filtra o DataFrame para manter apenas as linhas onde a primeira coluna contém valores de data válidos.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo a coluna "Date" como string.

    Retorna:
    --------
    pd.DataFrame
        DataFrame contendo apenas as linhas com datas válidas.
    """
    # Converter a primeira coluna para datetime, definindo erros='coerce' para ignorar valores inválidos
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Identificar a última linha válida (última data válida encontrada)
    last_valid_index = df["Date"].last_valid_index()

    # Se existir uma linha válida, cortamos o DataFrame até esse índice
    if last_valid_index is not None:
        df = df.loc[:last_valid_index]

    return df



def fill_missing_dates_and_times(df):
    """
    Preenche buracos nas colunas "Date" e "Time" garantindo que:
    1. Todas as datas do mês estejam presentes.
    2. Cada data tenha os 24 horários de 00:00 até 23:00.
    3. Mantém a estrutura das demais colunas preenchendo valores ausentes com NaN.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo pelo menos as colunas "Date" e "Time", onde:
        - "Date" deve estar no formato YYYY-MM-DD
        - "Time" deve estar no formato HH:00:00

    Retorna:
    --------
    pd.DataFrame
        DataFrame corrigido com todas as datas e horários preenchidos.
    """
    
    # Garantir que "Date" está no formato datetime e "Time" é string formatada
    df["Date"] = pd.to_datetime(df["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time"] = df["Time"].astype(str).str.zfill(8)  # Garante formato HH:00:00

    # Remover valores NaT na coluna "Date"
    df = df.dropna(subset=["Date"])

    # Determinar o ano e o mês baseado na coluna "Date"
    year = df["Date"].dt.year.mode()[0]
    month = df["Date"].dt.month.mode()[0]

    # Descobrir quantos dias o mês tem
    total_days = monthrange(year, month)[1]
    
    # Criar a lista completa de datas e horários esperados
    all_dates = pd.date_range(start=f"{year}-{month:02d}-01", periods=total_days, freq="D")
    all_times = [f"{h:02d}:00:00" for h in range(24)]

    # Criar um conjunto de registros existentes
    existing_records = set(zip(df["Date"].astype(str), df["Time"]))

    # Criar lista para armazenar as linhas que faltam
    missing_rows = []

    # Garantir que todas as datas e horários estejam presentes
    for date in all_dates:
        for time in all_times:
            if (str(date.date()), time) not in existing_records:
                # Criar uma linha vazia com NaN para todas as colunas, exceto Date e Time
                missing_row = {col: None for col in df.columns}
                missing_row["Date"] = date
                missing_row["Time"] = time
                missing_rows.append(missing_row)

    # Criar DataFrame com os valores ausentes
    missing_df = pd.DataFrame(missing_rows)

    # Concatenar o DataFrame original com os registros preenchidos e ordenar
    final_df = pd.concat([df, missing_df], ignore_index=True).sort_values(by=["Date", "Time"])

    return final_df


def generate_empty_month_dataframe(year, month, reference_df):
    """
    Gera um DataFrame vazio para um determinado mês e ano,
    preenchendo todas as datas e horários, mas com valores NaN nas demais colunas.

    Parâmetros:
    -----------
    year : int
        Ano para o qual o DataFrame será gerado.

    month : int
        Mês para o qual o DataFrame será gerado.

    reference_df : pd.DataFrame
        DataFrame de referência para manter a mesma estrutura de colunas.

    Retorna:
    --------
    pd.DataFrame
        DataFrame com todas as datas e horas do mês preenchidas, com valores NaN nas demais colunas.
    """

    # Obter o número total de dias no mês
    total_days = monthrange(year, month)[1]

    # Criar a lista completa de datas e horários esperados
    all_dates = pd.date_range(start=f"{year}-{month:02d}-01", periods=total_days, freq="D")
    all_times = [f"{h:02d}:00:00" for h in range(24)]

    # Criar uma lista para armazenar os dados
    empty_rows = []

    # Garantir que todas as datas e horários sejam preenchidos
    for date in all_dates:
        for time in all_times:
            empty_row = {col: None for col in reference_df.columns}  # Criar linha vazia com NaN
            empty_row["Date"] = date
            empty_row["Time"] = time
            empty_rows.append(empty_row)

    # Criar DataFrame com os valores ausentes
    empty_df = pd.DataFrame(empty_rows)

    return empty_df


def merge_and_save_dataframes(dfs, output_filename):
    """
    Concatena todos os DataFrames no dicionário dfs, ordenando por "Date" e "Time",
    e salva o resultado em um arquivo Excel.

    Parâmetros:
    -----------
    dfs : dict
        Dicionário contendo DataFrames (chave = nome, valor = DataFrame).

    output_filename : str
        Nome do arquivo Excel onde o DataFrame final será salvo.

    Retorna:
    --------
    pd.DataFrame
        O DataFrame final concatenado e ordenado.
    """

    # Concatenar todos os DataFrames
    final_df = pd.concat(dfs.values(), ignore_index=True)

    # Ordenar por "Date" e "Time"
    final_df = final_df.sort_values(by=["Date", "Time"])

    # Salvar em um arquivo Excel
    final_df.to_excel(output_filename, index=False)

    return final_df
