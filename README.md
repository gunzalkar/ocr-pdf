OCR PDF IT CAN BE USED ON ANY TYPE OF PDF EVEN EXTEMELY COMPRESSED PDF'S AS IT RECREATED THE PDF FROM INFLATING THE IMAGES.


chmod +x install_mac.sh or chmod +x install_ubuntu.sh

./install_mac.sh or ./install_ubuntu.sh

For windows 
  Install Tesseract (https://digi.bib.uni-mannheim.de/tesseract/?C=M;O=D)
  
  Install GhostScript ( https://ghostscript.com/releases/gsdnld.html )

  Change the installation location in the ocr_pdf.py line 18 of ghost script bin location comment 19th line and uncomment 18th. 

  pip3 install -r req.txt

python3 ocr_pdf.py "/full/location/to/source/folder" "/full/location/to/destination/folder"

NOTE : It will OCR all the pdf's inside the folder and further inside if pdfs exist. It will move all blank folders to a folder name blank_folder if they exist from the source folder. 
