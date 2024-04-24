import os
import tempfile
import boto3
import openai
import streamlit as st
import json

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AWS_REGION = 'us-east-1'

# AWS setup
boto3.setup_default_session(region_name=AWS_REGION)

# AWS clients
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')

QUERY_DICT = {
    "First Name": "First name of the person",
    "Middle Name": "Middle name of the person. Leave empty if not applicable.",
    "Last Name": "Last name of the person",
    "Date of Birth": "Date of birth of the person in MM-DD-YYYY format",
    "Address": "Full Address including state, zip-code, country, street and apartment address",
    "Organization": "affiliated organization name"
}

def extract_text_with_textract(image_bytes):
    """Use AWS Textract to analyze an ID document and extract key-value pairs."""
    response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
    fields = response['IdentityDocuments'][0]['IdentityDocumentFields']
    return {field['Type']['Text'] if 'Text' in field['Type'] else 'Unknown': field['ValueDetection']['Text']
            for field in fields if 'ValueDetection' in field}

def analyze_text(image_bytes):
    """Analyze the document text for entities using OpenAI and AWS Comprehend."""
    response = textract_client.analyze_document(Document={'Bytes': image_bytes}, FeatureTypes=['FORMS'])
    full_text = ' '.join(item['Text'] for item in response['Blocks'] if item['BlockType'] in ['WORD', 'LAYOUT_SECTION_HEADER'])
    return full_text

def get_entities_from_openai(text, query_dict):
    """Extract entities using OpenAI model."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Partition and extract all the given text to fit in values for the given keys."},
                  {"role": "user", "content": f"Extract all the given text to fit in values for the given keys. Return the JSON Object. Don't hallucinate. Keys and Descriptions: {query_dict} Text: {text}"}],
        max_tokens=150,
    )
    return response.choices[0].message.content

def get_entities_from_comprehend(text):
    """Extract entities using AWS Comprehend."""
    response = comprehend_client.detect_entities(Text=text, LanguageCode='en')
    return {entity['Type']: entity['Text'] for entity in response['Entities']}

def merge_entities(comprehend_entities, openai_entities):
    """Merge entity dictionaries."""
    return {**comprehend_entities, **openai_entities}

def process_id_document(image_bytes):
    """Process an ID document to extract and analyze data."""
    extracted_data = extract_text_with_textract(image_bytes)
    st.write("Extracted Data:", extracted_data)
    id_type = extracted_data.get('ID_TYPE')
    st.write("document_type:", id_type)

    if id_type == 'UNKNOWN':
        full_text = analyze_text(image_bytes)
        # comprehend_entities = get_entities_from_comprehend(full_text)
        # st.write("Comprehend Entities:", comprehend_entities)
        openai_entities = get_entities_from_openai(full_text, QUERY_DICT)
        st.write("OpenAI Entities:", openai_entities)
        # merged_entities = merge_entities(comprehend_entities, json.loads(openai_entities))  # Safer than eval
        # extracted_data.update(merged_entities)
        return json.loads(openai_entities)

    return {'DocumentType': id_type, **extracted_data}

def main():
    """Main function to run the Streamlit app."""
    st.title("ID Document Information Extractor")
    img_file_buffer = st.camera_input("Take a picture of your ID")

    if img_file_buffer is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(img_file_buffer.getvalue())
            tmp.seek(0)
            image_bytes = tmp.read()
            extracted_data = process_id_document(image_bytes)
            st.write("Extracted Structured Data:", extracted_data)

            if extracted_data:
                st.success("Information extracted successfully.")
            else:
                st.error("Failed to extract information. Please try another document.")

if __name__ == "__main__":
    main()
