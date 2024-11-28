import boto3
import config
from gspread_array_map import GsheetArrayMap, get_sheet_url
from metadata_processor import MetadataProcessor

class AddShortDesc(MetadataProcessor):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)
        # Path to your service account credentials JSON file
        creds_file = './sbx-kendra-8e724bd9a0ce.json'

        # Field to use as the key in the returned dictionary
        # Instantiate the GspreadArrayMap class
        self.gspread_map = GsheetArrayMap(creds_file)
        
        # 50 states
        self.logger.info("Reading 50 state")
        sheet_url = get_sheet_url('1pvqmNPP_22wvKdiCYFqcj1z55Z3lgZOX0nDDHhmmIZg')
        worksheet_name = 'Individual doc links'
        wanted_fields = ['State', 'Link', 'Description', 'Regulation Name']
        docs = self.gspread_map.get_fields(sheet_url, wanted_fields, worksheet_name)
        self.desc_dict = {}
        for doc in docs:
            try: 
                dict_entry = {
                    'Description': doc['Description'],
                    'Regulation Name': doc['Regulation Name'],
                    'State': doc['State']
                }
                self.desc_dict[doc['Link']] = dict_entry
            except KeyError:
                self.logger.error(f"KeyError: {doc['Link']}")

    def process(self, metadata):
        try: 
            new_title = []
            attributes = metadata.get('Attributes')
            uri = attributes.get('_source_uri')
            stuff = self.desc_dict.get(uri, None)
            if not stuff:
                raise Exception(f'uri {uri} not found.  Probably redirected')
            new_title.append(stuff.get('State', ''))
            attributes['jurisdiction'] = stuff.get('State', '')
            new_title.append(str(stuff.get('Regulation Name', '')))
            attributes['title'] = str(stuff.get('Regulation Name', ''))
            new_title.append(stuff.get('Description', ''))
            attributes['description'] = stuff.get('Description', '')
            # Build comprehensive title
            temp = " - ".join(s.strip() for s in new_title if s.strip())
            attributes['_document_title'] = temp[:1024]
            metadata['Attributes'] = attributes
        except Exception as e:
            self.logger.error(f"Error in child processor metadata: {e}")
            return None
        return metadata

def main():
    bucket_name = config.bucket_name

    # Use the custom processor
    processor = AddShortDesc(bucket_name)

    errors = processor.process_all_metadata_files()

    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)

if __name__ == "__main__":
    main()        