#BLANK FOLDER --> PDF --> IMAGE --> PDF --> BOOKMARKING --> OCR --> COMPATIBILITY PDF 1.4
#USES POOL PROCESSING 
import sys
import os
import fitz  # type: ignore
import img2pdf  # type: ignore
from PIL import Image
import shutil
import csv
from pypdf import PdfReader  # type: ignore
from typing import Dict, Union
import PyPDF2
import pandas as pd
import subprocess
import concurrent.futures
from joblib import Parallel, delayed

#ghost_script = rf"C:\Program Files\gs\gs10.03.1\bin\gswin64c.exe"
ghost_script = rf"gs"

def process_page(pdf_path, page_num, output_folder, dpi):
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(os.path.join(output_folder, f"page_{page_num + 1}.png"))
    pdf_document.close()

def pdf_to_images(pdf_path, output_folder, dpi=200):
    pdf_document = fitz.open(pdf_path)
    page_count = len(pdf_document)
    print("Processing :", pdf_path)
    Parallel(n_jobs=-1)(delayed(process_page)(pdf_path, page_num, output_folder, dpi) for page_num in range(page_count))
    pdf_document.close()

def convert_to_pdf(image_folder, pdf_name, output_folder):
    print("Processing:", pdf_name)
    image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.png', '.jpeg', '.jpg'))]
    image_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split("_")[1]))
    with open(os.path.join(output_folder, f"{pdf_name}.pdf"), "wb") as pdf_file:
        pdf_file.write(img2pdf.convert([open(image, "rb") for image in image_files]))

def images_to_pdf(image_folders, output_folder, pdf_names):
    Parallel(n_jobs=-1)(delayed(convert_to_pdf)(image_folder, pdf_name, output_folder) for image_folder, pdf_name in zip(image_folders, pdf_names))

def process_pdfs(source_folder, destination_folder):
    image_folders = []
    pdf_names = []
    skipped_files = []
    for root, _, files in os.walk(source_folder):
        for pdf_file in files:
            if pdf_file.lower().endswith('.pdf') and not pdf_file.startswith('.'):
                pdf_name = os.path.splitext(pdf_file)[0]
                print("Processing PFD :", pdf_file)
                pdf_path = os.path.join(root, pdf_file)
                relative_path = os.path.relpath(root, source_folder)
                output_folder = os.path.join(destination_folder, relative_path, pdf_name)
                os.makedirs(output_folder, exist_ok=True)
                try:
                    pdf_to_images(pdf_path, output_folder)
                    image_folders.append(output_folder)
                    pdf_names.append(os.path.join(relative_path, pdf_name))
                except Exception as e:
                    print(f"Skipping {pdf_file} due to error: {e}")
                    #skipped_files.append((padf_path, os.path.join(destination_folder, relative_path, pdf_file)))
    print("Converting image to pdfs...")
    images_to_pdf(image_folders, destination_folder, pdf_names)
    print("Converted!")
    for folder in image_folders:
        shutil.rmtree(folder)
    for src, dest in skipped_files:
        shutil.copy2(src, dest)  # Copy skipped files directly to maintain quality

def convertPDF2OCR(source_file, destination_file):
    try:
        ocr_command = f'ocrmypdf "{source_file}" "{destination_file}" -l eng+hin -O 3  --redo-ocr --output-type pdf -v'
        subprocess.run(ocr_command, shell=True, check=True)
    except Exception as e:
        print(f"Error processing {source_file}: {e}")

def process_file(source_file, destination_file):
    os.makedirs(os.path.dirname(destination_file), exist_ok=True)
    convertPDF2OCR(source_file, destination_file)

def bookmark_dict(
    bookmark_list, reader: PdfReader, use_labels: bool = False,
) -> Dict[Union[str, int], str]:
    result = {}
    for item in bookmark_list:
        if isinstance(item, list):
            result.update(bookmark_dict(item, reader))
        else:
            page_index = reader.get_destination_page_number(item)
            page_label = reader.page_labels[page_index]
            if use_labels:
                result[page_label] = item.title
            else:
                result[page_index] = item.title
    return result

def add_bookmark(pdf_file_path, csv_file_path, output_pdf_file):
    df = pd.read_csv(csv_file_path)
    pdf_reader = PyPDF2.PdfReader(pdf_file_path)
    output_pdf = PyPDF2.PdfWriter()
    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        output_pdf.add_page(page)
    for index, row in df.iterrows():
        page_number = int(row["Page Number"])
        title = row["Title"]
        output_pdf.add_outline_item(title, page_number - 1)
    with open(output_pdf_file, "wb") as f:
        output_pdf.write(f)
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)
    else:
        print(f"CSV file '{csv_file_path}' does not exist.")
    print("Bookmarks added to the PDF file successfully!")

def bookmark_main(input_folder, output_folder, storer):
    for root, _, files in os.walk(input_folder):
        for pdf_path in files:
            if pdf_path.lower().endswith(".pdf"):
                filename = pdf_path.rsplit(".", 1)[0]
                pdf_loc = os.path.join(root, pdf_path)
                relative_path = os.path.relpath(root, input_folder)
                out_loc = os.path.join(output_folder, relative_path, pdf_path)
                out_loc_2 = os.path.join(storer, relative_path, pdf_path)
                os.makedirs(os.path.dirname(out_loc_2), exist_ok=True)
                try:
                    reader = PdfReader(pdf_loc)
                except Exception as e:
                    print(f"Skipping {pdf_path} due to error: {e}")
                    shutil.copy2(pdf_loc, out_loc_2)  # Copy skipped files directly to maintain quality
                    continue
                
                if not reader.pages:
                    print(f"Skipping {pdf_path} as it has no pages.")
                    shutil.copy(pdf_loc, out_loc_2)
                    continue

                if reader.outline:
                    bms = bookmark_dict(reader.outline, reader, use_labels=True)
                    csv_loc = os.path.join(root, filename + ".csv")
                    print(filename)
                    if bms:
                        with open(csv_loc, "w", newline="") as csvfile:
                            fieldnames = ["Page Number", "Title"]
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            for page_nb, title in sorted(bms.items(), key=lambda n: f"{str(n[0]):>5}"):
                                writer.writerow({"Page Number": page_nb, "Title": title})
                        add_bookmark(out_loc, csv_loc, out_loc_2)
                    else:
                        print(f"No bookmarks found in {pdf_path}. Skipping.")
                        shutil.copy(out_loc, out_loc_2)
                else:
                    print(f"Skipping {pdf_path} as it has no bookmarks.")
                    shutil.copy(out_loc, out_loc_2)

def compress_pdf(input_pdf, output_pdf, image_downsampling="Bicubic", image_resolution=72, embed_fonts=False):
    command = [
        ghost_script,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-dColorImageDownsampleType=/{image_downsampling}",
        f"-dColorImageResolution={image_resolution}",
        f"-dGrayImageDownsampleType=/{image_downsampling}",
        f"-dGrayImageResolution={image_resolution}",
        f"-dMonoImageDownsampleType=/{image_downsampling}",
        f"-dMonoImageResolution={image_resolution}",
        "-sOutputFile=" + output_pdf,
    ]

    if not embed_fonts:
        command.append("-dEmbedAllFonts=false")

    subprocess.run(command + [input_pdf])

def compress_pdfs_in_folder(input_folder, output_folder):
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".pdf"):
                input_file = os.path.join(root, filename)
                relative_path = os.path.relpath(root, input_folder)
                output_file = os.path.join(output_folder, relative_path, filename)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                compress_pdf(input_file, output_file, image_resolution=100)

def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"Folder {folder_path} and its contents deleted successfully.")
    except FileNotFoundError:
        print(f"Folder {folder_path} does not exist.")

if __name__ == "__main__":
    source_folder = sys.argv[1]
    source_folder_bk = sys.argv[1]
    destination_folder = sys.argv[2]
    del_loc = sys.argv[2]
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    print("Processing PDFs...")
    process_pdfs(source_folder, destination_folder)
    print("Processed PDFs...")
    source_folder = os.path.join(destination_folder)
    tempo = os.path.join(del_loc, "tempo")
    if not os.path.exists(tempo):
        os.makedirs(tempo)
    bookmark_main(source_folder_bk, destination_folder, tempo)
    destination_folder = os.path.join(destination_folder, "temp_folder_ocr")
    source_folder = tempo
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    files_to_process = [(os.path.join(root, file), os.path.join(destination_folder, os.path.relpath(root, source_folder), file))
                        for root, _, files in os.walk(source_folder) for file in files if file.lower().endswith('.pdf')]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_file, source, destination) for source, destination in files_to_process]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"File processing generated an exception: {exc}")

    for filename in os.listdir(del_loc):
        if filename.lower().endswith(".pdf"):
            os.remove(os.path.join(del_loc, filename))

    delete_folder(tempo)
    compress_pdfs_in_folder(destination_folder, del_loc)
    delete_folder(destination_folder)
    
    count_folders_and_files(del_loc)
    print("Done with All the Files!")
    