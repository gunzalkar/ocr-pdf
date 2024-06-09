#!/bin/bash
sudo apt update
sudo apt-get upgrade -y
sudo apt-get update && sudo apt-get install -y python3
sudo apt-get install -y python3-pip
sudo apt-get install -y ghostscript
sudo apt-get install pngquant -y
sudo apt-get install tesseract -y
sudo apt-get install tesseract-ocr-hin -y
pip3 install pymupdf img2pdf pillow pypdf pandas joblib ocrmypdf pypdf2