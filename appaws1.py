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

def aws_extract_text(image_bytes):
    response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
    #response2 = textract_client.get_document_text_detection()
    print(response)
    return ' '.join([item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE'])

#def aws_comprehend_pii(text):
    response = comprehend_client.detect_entities(Text=text, LanguageCode='en')
    pii_data = {"Name": [], "DOB": [], "Address": []}
    for entity in response['Entities']:
        if entity['Type'] == 'PERSON':
            pii_data["Name"].append(entity['Text'])
        elif entity['Type'] == 'DATE':
            pii_data["DOB"].append(entity['Text'])
        elif entity['Type'] in ['LOCATION', 'ADDRESS']:
            pii_data["Address"].append(entity['Text'])
    return pii_data

def aws_comprehend_pii(text):
    response = comprehend_client.detect_entities(Text=text, LanguageCode='en')
    pii_data = {"Name": [], "DOB": [], "Address": [], "Sex": [], "Other": []}
    for entity in response['Entities']:
        if entity['Type'] == 'PERSON':
            pii_data["Name"].append(entity['Text'])
        elif entity['Type'] == 'DATE':
            pii_data["DOB"].append(entity['Text'])
        elif entity['Type'] in ['LOCATION', 'ADDRESS']:
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
            extracted_text = aws_extract_text(tmp.read())
            st.write(extracted_text)

        if extracted_text:
            parsed_data = aws_comprehend_pii(extracted_text)
            df = pd.DataFrame([parsed_data])
            
            if check_file_exists(bucket_name, file_name):
                append_to_s3(df, bucket_name, file_name)
            else:
                upload_to_s3(df, bucket_name, file_name)

            st.success("Extracted information saved to S3 bucket.")

if __name__ == "__main__":
    main()
