import os, boto3, openai, json, base64

# Constants
openai.api_key = os.environ['OPENAI_API_KEY']
AWS_REGION = 'us-east-1'
QUERY_DICT = {
    "ID_TYPE": "The type of the identification document provided.",
    "FIRST_NAME": "First name of the person.",
    "MIDDLE_NAME": "Middle name of the person. Leave empty if not applicable.",
    "LAST_NAME": "Last name of the person.",
    "DATE_OF_BIRTH": "Date of birth of the person in MM-DD-YYYY format",
    "ADDRESS": "The address line 1 includes the street, street number and apartment/suite information.",
    "ORGANIZATION": "Name of the person's affiliated organization.",
    "ZIP_CODE_IN_ADDRESS": "The zip code of the person's address."
}
REQUIRED_FIELDS = ['ID_TYPE', 'FIRST_NAME', 'LAST_NAME', 'DATE_OF_BIRTH', 'ADDRESS', 'ZIP_CODE_IN_ADDRESS']
ADDITIONAL_INFO_FIELD = 'ADDITIONAL_INFORMATION'

# AWS setup
boto3.setup_default_session(region_name=AWS_REGION)

# AWS clients
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')

def extract_text_with_textract(image_bytes) -> dict:
    """Use AWS Textract to analyze an ID document and extract key-value pairs."""
    response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
    fields = response['IdentityDocuments'][0]['IdentityDocumentFields']
    return {field['Type']['Text'] if 'Text' in field['Type'] else 'Unknown': field['ValueDetection']['Text'] for field in fields if 'ValueDetection' in field}

def analyze_text(image_bytes):
    """Analyze the document text for entities using OpenAI and AWS Comprehend."""
    response = textract_client.analyze_document(Document={'Bytes': image_bytes}, FeatureTypes=['FORMS'])
    full_text = ' '.join(item['Text'] for item in response['Blocks'] if item['BlockType'] in ['WORD', 'LAYOUT_SECTION_HEADER'])
    return full_text

def get_entities_from_openai(text, query_dict) -> dict:
    """Extract entities using OpenAI model."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Partition and extract all the given text to fit in values for the given keys."},
                  {"role": "user", "content": f"Extract all the given text to fit in values for the given keys. Return the JSON Object. Don't hallucinate. Keys and Descriptions: {query_dict} Text: {text}"}],
        max_tokens=150,
    )
    return json.loads(response.choices[0].message.content)

def get_entities_from_comprehend(text):
    """Extract entities using AWS Comprehend."""
    response = comprehend_client.detect_entities(Text=text, LanguageCode='en')
    return {entity['Type']: entity['Text'] for entity in response['Entities']}

def merge_entities(comprehend_entities, openai_entities):
    """Merge entity dictionaries."""
    return {**comprehend_entities, **openai_entities}

def process_id_document(image_bytes):
    """Process an ID document to extract and analyze data."""
    response_dict = dict()
    response_dict[ADDITIONAL_INFO_FIELD] = dict()
    entities = extract_text_with_textract(image_bytes)
    if entities['ID_TYPE'] == 'UNKNOWN':
        full_text = analyze_text(image_bytes)
        entities = get_entities_from_openai(full_text, REQUIRED_FIELDS)
    for key, value in entities.items():
        if key in REQUIRED_FIELDS:
            response_dict[key] = value
        else:
            response_dict[ADDITIONAL_INFO_FIELD][key] = value
    return response_dict

def lambda_handler(event, context):
    image_data = base64.b64decode(event['body'])
    response = process_id_document(image_data)
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }