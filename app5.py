#OCR through CV2 & Parsing extracted text through NER - spacy library
import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
import tempfile
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_lg")

def extract_text(image):
    # Convert the image to gray scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    # OCR using Tesseract on the thresholded image
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    return text

def parse_extracted_text(text):
    doc = nlp(text)
    pii_data = {"Name": "Not found", "DOB": "Not found", "Address": "Not found"}

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            pii_data["Name"] = ent.text
        elif ent.label_ == "DATE":
            pii_data["DOB"] = ent.text
        elif ent.label_ == "GPE" or ent.label_ == "LOC":
            pii_data["Address"] = ent.text

    return pii_data

def main():
    st.title("ID Card Information Extractor")
    img_file_buffer = st.camera_input("Take a picture")

    if img_file_buffer is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(img_file_buffer.getvalue())
            image = cv2.imread(tmp.name)

        st.image(image, channels="BGR", caption="Captured Image")
        extracted_text = extract_text(image)
        st.write("Extracted Text:", extracted_text)

        parsed_data = parse_extracted_text(extracted_text)
        for key, value in parsed_data.items():
            st.write(f"{key}: {value}")

        if st.button("Save to sheet"):
            df = pd.DataFrame([parsed_data])
            df.to_csv("extracted_info.csv", mode='a', header=False, index=False)
            st.success("Saved to sheet")

if __name__ == "__main__":
    main()
