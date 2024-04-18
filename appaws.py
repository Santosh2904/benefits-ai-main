#OCR through textract & NER through comprehend. Information gets stored in S3 bucket. 
import streamlit as st
import boto3
import pandas as pd
import io
import tempfile

# Initialize AWS clients for Textract and Comprehend
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')
s3_client = boto3.client('s3')

bucket_name = 'benefitsai'  # Replace with your S3 bucket name
file_name = 'extracted_pii.csv'      # The CSV file where data will be stored

# def aws_extract_text(image_bytes):
#     response = textract_client.analyze_document(Document={'Bytes': image_bytes}, FeatureTypes=['LAYOUT'])
#     # Include both 'LINE' and 'LAYOUT_SECTION_HEADER' block types in the extracted text
#     relevant_text = [item['Text'] for item in response['Blocks'] if item['BlockType'] in ['WORD', 'LAYOUT_SECTION_HEADER']]
#     return ' '.join(relevant_text)

# def aws_analyze_id(image_bytes):
#     response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
#     print(response)
#     fields = response['IdentityDocuments'][0]['IdentityDocumentFields']
#     extracted_data = {}
#     for field in fields:
#         if 'ValueDetection' in field:
#             key = field['Type']['Text']
#             value = field['ValueDetection']['Text']
#             extracted_data[key] = value
            
#             # extracted_text = ""
#             # for key, value in extracted_data.items():
#             #     extracted_text += f"{key}: {value}\n"

#     return extracted_data

def aws_analyze_id(image_bytes):
    # Initialize the Textract client
    textract_client = boto3.client('textract')
    
    # Call AnalyzeID API
    response = textract_client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
    
    # Debugging print, can be commented out in production
    print(response)
    
    # Handle the fields from the response
    fields = response['IdentityDocuments'][0]['IdentityDocumentFields']
    extracted_data = {}
    
    for field in fields:
        # Check if 'ValueDetection' exists and has text content
        if 'ValueDetection' in field and 'Text' in field['ValueDetection']:
            # Use 'Type' key to describe the 'Text' content if available
            # Otherwise use 'Unknown'
            key = field['Type']['Text'] if 'Text' in field['Type'] else 'Unknown'
            value = field['ValueDetection']['Text']
            extracted_data[key] = value
    
    return extracted_data

def extract_personal_info(data):
    # Extracting the full name
    full_name = " ".join([data.get("FIRST_NAME", ""),
                          data.get("MIDDLE_NAME", ""),
                          data.get("LAST_NAME", "")]).strip()

    # Extracting the full address
    full_address = ", ".join([data.get("ADDRESS", ""),
                              data.get("CITY_IN_ADDRESS", ""),
                              data.get("STATE_NAME", ""),
                              data.get("ZIP_CODE_IN_ADDRESS", "")]).strip(", ")

    # Extracting the date of birth
    date_of_birth = data.get("DATE_OF_BIRTH", "")

    return full_name, full_address, date_of_birth

def aws_comprehend_pii(text):
    response = comprehend_client.detect_entities(Text='str', LanguageCode='en')
    pii_data = {"Name": [], "DOB": [], "Address": [], "Other": []}
    for entity in response['Entities']:
        if entity['Type'] == 'PERSON':
            pii_data["Name"].append(entity['Text'])
        elif entity['Type'] == 'DATE':
            pii_data["DOB"].append(entity['Text'])
        elif entity['Type'] == 'LOCATION':
            pii_data["Address"].append(entity['Text']) 
        elif entity['Type'] == 'OTHER':
            pii_data["Other"].append(entity['Text'])

    return pii_data


def check_file_exists(bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False

def upload_to_s3(data_frame, bucket, key):
    out_buffer = io.StringIO()
    data_frame.to_csv(out_buffer, index=False)
    s3_client.put_object(Bucket=bucket, Key=key, Body=out_buffer.getvalue())

def append_to_s3(data_frame, bucket, key):
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
            extracted_data = aws_analyze_id(tmp.read())
            st.write("Extracted Structured Data:", extracted_data)

        if extracted_data:
            parsed_data = aws_comprehend_pii(extracted_data)
            st.write(parsed_data)
            df = pd.DataFrame([parsed_data])
            
            if check_file_exists(bucket_name, file_name):
                append_to_s3(df, bucket_name, file_name)
            else:
                upload_to_s3(df, bucket_name, file_name)

            st.success("Extracted information saved to S3 bucket.")

if __name__ == "__main__":
    main()
