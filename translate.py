from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from PyPDF2 import PdfReader
from fpdf import FPDF
from PIL import Image
import nltk
from nltk.translate.bleu_score import SmoothingFunction, corpus_bleu, sentence_bleu
import requests
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

user_bucket = os.environ.get('USER_BUCKET_NAME')

def add_text_images(text_list, my_size, my_font, my_page, is_last_record):
    # print(text_list)
    # print(my_size)
    # print(my_font)
    # print(my_page)

    image_list=[]
    if os.path.exists("images"):
        # Loop through all files in the directory
        for filename in os.listdir("images"):
            if filename.endswith(".png"):
                image_list.append(filename)  # Add the full path of the image file to the list
        page_list=[]
        for file in image_list:
            page_list.append(file.split("_")[0])

    if (pdf.page_no()<my_page+1):
        pdf.add_page()
    
    pdf.set_font(my_font, size=my_size)
    for text in text_list:
        # Replace problematic characters with a replacement character
        text = text.encode('latin-1', errors='replace').decode('latin-1')

        # Split the text into multiple lines
        lines = text.split('\n')

        # Output each line using MultiCell
        for line in lines:
            pdf.multi_cell(0, 5, line)

    if (is_last_record):
        if os.path.exists("images"):
            for image_page in page_list:
                # Add a blank line
                pdf.cell(5, 10, '')
                if (int(image_page) == pdf.page_no()):
                    # Get the current cursor position
                    current_y = pdf.get_y()

                    for image_file in image_list:
                        if ( image_file.split("_")[0] == image_page):
                            my_filename = "images/" + image_file
                            img = Image.open(my_filename)
                            width, height = img.size
                            if width > height:
                                ratio = 100 / width
                            else:
                                ratio = 190 / height
                            width *= ratio
                            height *= ratio
                            pdf.image(my_filename, x=10, y=current_y, w=width, h=height)
                            
                            # Add a blank line
                            pdf.cell(5, 10, '')

                            image_list.remove(image_file)

                    # Add a blank line
                    pdf.cell(5, 10, '')

def google_translate_text(target, text, current_font, current_size, current_page, is_last_record):

    url = "https://google-translator9.p.rapidapi.com/v2"

    payload = {
        "q": text,
        "target": target,
        "source": "en",
        "format": "text"
    }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": os.environ.get('RAPID_API_HOST')
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()

    # print("Translated text: " + response["data"]["translations"][0]["translatedText"])
    # print("Size: " + str(current_size))
    # print("Family: ", current_font)
    # print("Page: ", current_page)
    # print("=================================================================================")

    add_text_images([response["data"]["translations"][0]["translatedText"]], current_size, current_font, current_page, is_last_record)


def text_processing(Extract_Font, Extract_Size, Extract_Data, Extract_page):

    for i in range(len(Extract_Font)):
        if ("Times" in Extract_Font[i]):
            Extract_Font[i]='Times'
        elif ("Zap" in Extract_Font[i]):
            Extract_Font[i]='ZapfDingbats'
        elif ("Courier" in Extract_Font[i]):
            Extract_Font[i]='Courier'
        elif ("Helvetica" in Extract_Font[i]):
            Extract_Font[i]='Helvetica'
        elif ("Arial" in Extract_Font[i]):
            Extract_Font[i]='Arial'
        elif ("Symbol" in Extract_Font[i]):
            Extract_Font[i]='Symbol'
        else:
            Extract_Font[i]='Times'

    i=0
    current_size=Extract_Size[0]
    current_font=Extract_Font[0]
    current_data=""
    current_page=Extract_page[0]

    while i<len(Extract_Size):
        current_size=Extract_Size[i]
        current_font=Extract_Font[i]
        current_data=Extract_Data[i]
        current_page=Extract_page[i]

        c=1
        for j in range(i+1, len(Extract_Size)):
            if (( current_size == Extract_Size[j] ) and ( current_font == Extract_Font[j] ) and ( current_page == Extract_page[j] )):
                current_data = current_data + Extract_Data[j]
                c+=1
            elif (current_page != Extract_page[j]):
                google_translate_text("fr", current_data, current_font, current_size, current_page, True)
                current_data=""
                break
            else:
                google_translate_text("fr", current_data, current_font, current_size, current_page, False)
                current_data=""
                break
        i=i+c
    
    if (current_data!=""):
        google_translate_text("fr", current_data, current_font, current_size, current_page, True)

def extract_images(path, Extract_Font, Extract_Size, Extract_Data, Extract_page):
    with open(path,"rb") as f:
        reader = PdfReader(f)

        has_images = False
        for page in reader.pages:
            if page.images:
                has_images = True
                break
        if has_images:
            # print("The PDF contains at least one image.")

            if not os.path.exists("images"):
                os.makedirs("images")

            for page_num in range(0,len(reader.pages)):
                selected_page = reader.pages[page_num]
                for i, img_file_obj in enumerate(selected_page.images):
                    with open('images/'+str(page_num+1)+"_image_"+str(i)+".png", "wb") as out:
                        out.write(img_file_obj.data)

    text_processing(Extract_Font, Extract_Size, Extract_Data, Extract_page)


def extract_text(path):
    Extract_Font=[]
    Extract_Size=[]
    Extract_Data=[]
    Extract_page=[]

    for i, page_layout in enumerate(extract_pages(path)):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                Font_size=character.size
                                Font_style=character.fontname
                    except:
                        pass
                Extract_Font.append(Font_style)
                Extract_Size.append(int(Font_size))
                Extract_Data.append(element.get_text())
                Extract_page.append(i)
    # print(Extract_page)
    extract_images(path, Extract_Font, Extract_Size, Extract_Data, Extract_page)

if __name__=="__main__":

    filename="documentation.pdf"
    # Download the file from S3
    s3client.download_file(user_bucket, filename, filename)

    pdf = FPDF()
    pdf.add_page()

    extract_text(filename)

    pdf.output(filename.split(".")[0]+"_translated.pdf")

    # Upload the file to S3
    with open(filename.split(".")[0]+"_translated.pdf", 'rb') as f:
        s3client.upload_fileobj(f, user_bucket, filename.split(".")[0]+"_translated.pdf")

    os.remove(filename)
    os.remove(filename.split(".")[0]+"_translated.pdf")

    # Delete the images directory and all its contents
    if os.path.exists("images"):
        for filename in os.listdir("images"):
            file_path = os.path.join("images", filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)

        os.rmdir("images")