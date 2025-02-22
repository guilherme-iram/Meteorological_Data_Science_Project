import pandas as pd


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


def fill_missing_times(df):
    """
    Garante que para cada data única no DataFrame haja 24 registros correspondentes a cada hora do dia.
    
    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame contendo as colunas "Date" e "Time".
    
    Retorna:
    --------
    pd.DataFrame
        DataFrame com horários ausentes preenchidos.
    """
    
    # Converter a coluna "Date" para string e remover espaços extras
    df["Date"] = df["Date"].astype(str).str.strip()
    
    # Garantir que "Time" esteja no formato correto HH:00:00
    df["Time"] = df["Time"].astype(str).str.strip()
    df["Time"] = df["Time"].apply(lambda x: f"{x[:2]}:00:00" if len(x) >= 2 else x)

    all_times = [f"{str(h).zfill(2)}:00:00" for h in range(24)]  # Lista de horários esperados
    unique_dates = df["Date"].unique()
    filled_rows = []
    columns_name = [str(name) for name in df.columns]

    for date in unique_dates:
        existing_times = df[df["Date"] == date]["Time"].tolist()
        missing_times = sorted(list(set(all_times) - set(existing_times)))  # Garantir ordem correta

        for time in missing_times:
            dict_row = {k: None for k in columns_name}  # Criar linha vazia
            dict_row["Date"] = date
            dict_row["Time"] = time
            filled_rows.append(dict_row)

    # Criar DataFrame com os horários ausentes
    missing_df = pd.DataFrame(filled_rows)

    # Concatenar o original com os dados preenchidos, garantir ordenação e remover duplicatas
    final_df = pd.concat([df, missing_df], ignore_index=True).drop_duplicates().sort_values(by=["Date", "Time"])

    return final_df