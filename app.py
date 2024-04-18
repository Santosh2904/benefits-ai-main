import streamlit as st
import boto3
import pandas as pd
import io
import tempfile

# Initialize AWS clients
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')
s3_client = boto3.client('s3')

bucket_name = 'benefitsai'  # Your S3 bucket name
file_name = 'extracted_pii.csv'  # The CSV file where data will be stored

def aws_ocr(image_bytes):
    """Extracts information from an ID document using Textract and Comprehend."""
    # Analyze ID document with Textract
    analyze_id_response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
    fields = analyze_id_response['IdentityDocuments'][0]['IdentityDocumentFields']
    extracted_data = {field['Type']['Text'] if 'Text' in field['Type'] else 'Unknown': field['ValueDetection']['Text'] for field in fields if 'ValueDetection' in field}
    st.write(extracted_data)
    document_type = extracted_data.get('DocumentType', 'Unknown')
    pii_data = {"Name": [], "Address": [], "SEX": [], "ORGANIZATION": []}
    
    # Analyze document for relevant text with Textract
    analyze_document_response = textract_client.analyze_document(Document={'Bytes': image_bytes}, FeatureTypes=['FORMS'])
    relevant_text = ' '.join(item['Text'] for item in analyze_document_response['Blocks'] if item['BlockType'] in ['WORD', 'LAYOUT_SECTION_HEADER'])
    st.write(relevant_text)
    # Detect entities with Comprehend
    comprehend_response = comprehend_client.detect_entities(Text=relevant_text, LanguageCode='en')
    for entity in comprehend_response['Entities']:
        if entity['Type'] == 'PERSON':
            pii_data["Name"].append(entity['Text'])
        elif entity['Type'] == 'SEX':
            pii_data["SEX"].append(entity['Text'])
        elif entity['Type'] == 'LOCATION':
            pii_data["Address"].append(entity['Text']) 
        elif entity['Type'] == 'ORGANIZATION':
            pii_data["ORGANIZATION"].append(entity['Text'])

    # Check for SEX or SEX field from Textract, use Comprehend if not present
    SEX = extracted_data.get("SEX", "") or extracted_data.get("SEX", "")
    if not SEX:
        # Update SEX if found through Comprehend
        SEX = ' '.join(pii_data["SEX"]) if pii_data["SEX"] else ""

    # Organization is only populated if document type is unknown
    organization_name = ' '.join(pii_data["ORGANIZATION"]) if document_type == 'Unknown' else ""
    st.write(pii_data)
    # Construct full name and address
    full_name = " ".join([extracted_data.get("FIRST_NAME", ""), extracted_data.get("MIDDLE_NAME", ""), extracted_data.get("LAST_NAME", "")]).strip()
    full_address = ", ".join([extracted_data.get("ADDRESS", ""), extracted_data.get("CITY_IN_ADDRESS", ""), extracted_data.get("STATE_IN_ADDRESS", ""), extracted_data.get("ZIP_CODE_IN_ADDRESS", "")]).strip(", ")
    date_of_birth = extracted_data.get("DATE_OF_BIRTH", "")

    required_data = {
        'Name': full_name,
        'Address': full_address,
        'DOB': date_of_birth,
        'SEX': SEX,
        'ORGANIZATION': organization_name
    }

    return required_data

def upload_to_s3(data_frame, bucket, key):
    """Uploads data to an S3 bucket."""
    out_buffer = io.StringIO()
    data_frame.to_csv(out_buffer, index=False)
    s3_client.put_object(Bucket=bucket, Key=key, Body=out_buffer.getvalue())

def append_to_s3(data_frame, bucket, key):
    """Appends data to an existing CSV file in S3."""
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    existing_data = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')
    updated_data = pd.concat([existing_data, data_frame], ignore_index=True)
    upload_to_s3(updated_data, bucket, key)

def main():
    st.title("ID Card Information Extractor")
    img_file_buffer = st.camera_input("Take a picture")

    if img_file_buffer is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(img_file_buffer.getvalue())
            tmp.seek(0)
            image_bytes = tmp.read()
            extracted_data = aws_ocr(image_bytes)
            st.write("Extracted Structured Data:", extracted_data)

            df = pd.DataFrame([extracted_data])
            if s3_client.list_objects_v2(Bucket=bucket_name, Prefix=file_name)['KeyCount'] > 0:
                append_to_s3(df, bucket_name, file_name)
            else:
                upload_to_s3(df, bucket_name, file_name)

            st.success("Extracted information saved to S3 bucket.")

if __name__ == "__main__":
    main()
