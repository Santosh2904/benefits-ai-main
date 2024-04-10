#OCR through CV2 & Parsing extracted text through regex
import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
import tempfile
import re

# Enhanced Function to Extract Text from Image
def extract_text(image):
    # Convert the image to RGB and Grayscale
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2GRAY)

    # Applying Gaussian blur and thresholding
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)

    # Custom Tesseract configuration
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789%&$#@-?:()/;,*.\' "'

    # OCR using Tesseract on the thresholded image
    text = pytesseract.image_to_string(thresh, config=custom_config)

    return text

# Function to Parse Extracted Text
#def parse_extracted_text(text):
    # Example regular expressions; adjust based on actual ID formats
    # name_regex = r"Name:\s*([A-Za-z\s]+)"
    # dob_regex = r"Date of Birth:\s*(\d{2}/\d{2}/\d{4})"
    # address_regex = r"Address:\s*([\w\s,]+)"
    # sex_regex = r"Sex:\s*([MF])"
    # license_number_regex = r"License Number:\s*(\w+)"
    # state_id_regex = r"State ID:\s*(\w+)"
    # health_insurance_id_regex = r"Health Insurance ID:\s*(\w+)"

    # fields = {
    #     "Name": re.search(name_regex, text, re.IGNORECASE),
    #     "DOB": re.search(dob_regex, text, re.IGNORECASE),
    #     "Address": re.search(address_regex, text, re.IGNORECASE),
    #     "Sex": re.search(sex_regex, text, re.IGNORECASE),
    #     "License Number": re.search(license_number_regex, text, re.IGNORECASE),
    #     "State ID": re.search(state_id_regex, text, re.IGNORECASE),
    #     "Health Insurance ID": re.search(health_insurance_id_regex, text, re.IGNORECASE)
    # }

    # # Formatting the results
    # return {key: match.group(1) if match else "Not found" for key, match in fields.items()}

def parse_extracted_text(text):
    # Updated regex patterns
    name_regex = r"[A-Z]{2,}\s[A-Z]{2,}"
    dob_regex = r"\d{2}/\d{2}/\d{4}"
    address_regex = r"\d{1,5} [A-Za-z0-9\s,]+"

    name_match = re.search(name_regex, text)
    dob_match = re.search(dob_regex, text)
    address_match = re.search(address_regex, text)

    return {
        "Name": name_match.group(0) if name_match else "Not found",
        "DOB": dob_match.group(0) if dob_match else "Not found",
        "Address": address_match.group(0) if address_match else "Not found",
    }

# Main Streamlit Application
def main():
    st.title("ID Card Information Extractor")
    img_file_buffer = st.camera_input("Take a picture")

    if img_file_buffer is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(img_file_buffer.getvalue())
            image = cv2.imread(tmp.name)

        st.image(image, channels="BGR", caption="Captured Image")
        extracted_text = extract_text(image)
        st.write("OCR Extracted Text:", extracted_text)
        if extracted_text.strip():
            st.write("Extracted Text:", extracted_text)
            parsed_data = parse_extracted_text(extracted_text)
            st.write(parsed_data)
            for key, value in parsed_data.items():
                st.write(f"{key}: {value}")

            if st.button("Save to sheet"):
                df = pd.DataFrame([parsed_data])
                df.to_csv("extracted_info.csv", mode='a', header=False, index=False)
                st.success("Saved to sheet")
        else:
            st.warning("No text could be extracted from the image.")

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract"
    main()
