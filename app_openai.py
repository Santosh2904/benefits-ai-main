import streamlit as st
import boto3
import tempfile
import openai
import os

# AWS and OpenAI configuration
openai_api_key = os.getenv('OPENAI_API_KEY')
boto3.setup_default_session(region_name='us-east-1')  # specify your AWS region

# Initialize AWS clients
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')

def process_id_document(image_bytes):
    """Process an ID document to extract text and recognize entities."""
    analyze_id_response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
    fields = analyze_id_response['IdentityDocuments'][0]['IdentityDocumentFields']
    extracted_data = {field['Type']['Text'] if 'Text' in field['Type'] else 'Unknown': field['ValueDetection']['Text'] for field in fields if 'ValueDetection' in field}
    st.write(extracted_data)
    document_type = extracted_data.get('DocumentType', 'Unknown')

    if document_type == 'Unknown':
        analyze_document_response = textract_client.analyze_document(Document={'Bytes': image_bytes}, FeatureTypes=['FORMS'])
        full_text = ' '.join(item['Text'] for item in analyze_document_response['Blocks'] if item['BlockType'] in ['WORD', 'LAYOUT_SECTION_HEADER'])
        st.write(full_text)
        #extract text using aws analyze_document
        #full text will be the text extracted from the document
        #pass the full text to the openai api (or other apis like llama3 or cluade 3) and get the entities + pass it to comprehend & get the entities (have the option of using comprehend medical for health insurances)
        #merge the entities from comprehend and openai
        full_text = ' '.join([extracted_data[key] for key in extracted_data if key != 'Unknown'])
        comprehend_response = comprehend_client.detect_entities(Text=full_text, LanguageCode='en')
        comprehend_entities = {entity['Type']: entity['Text'] for entity in comprehend_response['Entities']}
        st.write("Comprehend Entities:", comprehend_entities)
 
        openai_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Extract entities from the following text."},
                    {"role": "user", "content": full_text}],
            max_tokens=150
        )

        openai_entities = openai_response['choices'][0]['message']['content'].strip()
        st.write("OpenAI Entities:", openai_entities)
        try:
            openai_entities_dict = eval(openai_entities)  # Ensure security checks as necessary
            if isinstance(openai_entities_dict, dict):
                merged_entities = {**comprehend_entities, **openai_entities_dict}
                extracted_data.update(merged_entities)
        except Exception as e:
            st.error(f"Error parsing entities from OpenAI response: {str(e)}")

    return {
        'DocumentType': document_type,
        **extracted_data
    }

def main():
    st.title("ID Document Information Extractor")
    img_file_buffer = st.camera_input("Take a picture")

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
