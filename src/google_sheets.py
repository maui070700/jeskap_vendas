from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from datetime import datetime

def get_credentials():
    key_file_path =  'src/key.json'
    if not os.path.isfile(key_file_path):
        raise FileNotFoundError(f"Arquivo secreto '{key_file_path}' não encontrado.")
    
    return service_account.Credentials.from_service_account_file(
        key_file_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

def insert_values(spreadsheet_id, range_name, value_input_option, values):
    creds = get_credentials()
    try:
        service = build("sheets", "v4", credentials=creds)
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        return result
    except HttpError as error:
        return str(error)
    
def get_rows(id_number):
    row_number = 0
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId='1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA',
        range=f"Pedidos!A1:R"
    ).execute()
    rows = result.get('values', [])
    

    for row in rows:
        row_number += 1
        if str(row[11]) == str(id_number):
            return row, row_number
    return None, None

def get_last_row(vendedora):
    lasts_ids = []
    vendedora_map = {
        'Raquel': 'Mercado Livre Site Raquel',
        'Thais': 'Thais - Organico Thais Tragego pago'
    }
    vendedora = vendedora_map.get(vendedora, vendedora)
    
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId='1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA',
        range="Pedidos!A1:R"
    ).execute()
    rows = result.get('values', [])
    
    filtered_rows = [
        row for row in rows if len(row) > 1 and row[1] in vendedora 
    ]
    lasts_rows = filtered_rows[-5:]
    for i in lasts_rows:
        lasts_ids.append(i[11])
        
    return '\n\n'.join(reversed(lasts_ids))

def get_rows_logista(id_number):
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    
    def get_sheet_values(sheet_range):
        """Fetch values from Google Sheets given a specific range."""
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId='1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA',
                range=sheet_range
            ).execute()
            return result.get('values', [])
        except Exception as e:
            print(f"Error fetching data from Google Sheets: {e}")
            return []

    def find_row_by_value(abas, column_index, multiple=False):
        """
        Find row(s) by matching value in a specific column.
        If multiple is True, return all matching rows.
        """
        rows = get_sheet_values(abas)
        matching_rows = []

        for idx, row in enumerate(rows, start=1): 
            if len(row) > column_index and str(row[column_index]) == str(id_number):
                if multiple:
                    matching_rows.append((row, idx))
                else:
                    return row, idx
        
        return matching_rows if multiple else (None, None)

    rows_geral, row_number_geral = find_row_by_value('Logista-Geral!A1:K', 5)

    items_rows = find_row_by_value('Logista-Itens!A1:H', 0, multiple=True)

    if rows_geral and items_rows:
        items_list = [row for row, idx in items_rows]
        row_numbers_itens = [idx for row, idx in items_rows]
        return rows_geral, row_number_geral, items_list, row_numbers_itens

    return None, None, None, None


def update_rows(sheet_range, values):
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId='1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA',
        valueInputOption="USER_ENTERED",
        body=body,
        range=sheet_range
    ).execute()
    return result
