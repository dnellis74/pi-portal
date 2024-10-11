import gspread
import logging
from google.oauth2.service_account import Credentials

class GsheetArrayMap:
    """
    A class to interact with Google Sheets using gspread and return filtered data.
    
    Attributes:
        client (gspread.Client): The authenticated gspread client.
    """

    def __init__(self, creds_file):
        """
        Initialize the GspreadArrayMap with the provided credentials file.
        
        Args:
            creds_file (str): The path to the Google service account credentials JSON file.
        
        Raises:
            Exception: If there is an error in authentication.
        """
        try:
            # Define the scope for reading spreadsheets
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            self.client = gspread.authorize(creds)
        except Exception as e:
            raise Exception(f"Authentication failed: {e}")

    def get_fields(self, sheet_url, wanted_fields, worksheet_name=None):
        """
        Retrieve filtered data from a Google Sheet.
        
        Args:
            sheet_url (str): The URL of the Google Sheet.
            wanted_fields (list of str): A list of column headers to retrieve.
            worksheet_name (str, optional): The name of the worksheet to access.
                If not provided, the first worksheet is used.
        
        Returns:
            array
        
        Raises:
            Exception: If the sheet cannot be accessed.
            ValueError: If wanted_fields do not match any columns in the sheet.
        """

        try:
            # Set up basic configuration
            logger = logging.getLogger(__name__)

            logger.info("Reading 50 state spreadsheet")
            # Open the Google Sheet
            sheet = self.client.open_by_url(sheet_url)
            # Access the specified worksheet or the first one
            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet = sheet.sheet1
            # Retrieve all records
            records = worksheet.get_all_records()
        except Exception as e:
            raise Exception(f"Failed to access the sheet: {e}")

        # Get the headers from the first row
        sheet_fields = worksheet.row_values(1)
        if not set(wanted_fields).issubset(set(sheet_fields)):
            raise ValueError("wanted_fields do not match any columns in the sheet.")

        result = []

        for index, record in enumerate(records):
            try:
                # Filter the record to include only wanted_fields
                filtered_record = {field: record[field] for field in wanted_fields}
                result.append(filtered_record)

            except Exception as row_error:
                logger.error(f"Error processing row {index + 2}: {row_error}")
                continue  # Continue processing the next row despite the error

        return result


def main():
    """
    Example usage of the GspreadArrayMap class.
    """
    creds_file = 'path/to/credentials.json'
    sheet_url = 'https://docs.google.com/spreadsheets/d/your_sheet_id_here/edit#gid=0'
    wanted_fields = ['Name', 'Email', 'Age']
    key_field = 'Email'

    try:
        gspread_map = GsheetArrayMap(creds_file)
        data = gspread_map.get_fields(sheet_url, wanted_fields, key_field)
        print(data)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
