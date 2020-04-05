import sys
from pdflatex import PDFLaTeX
texfile = sys.argv[1]
pdfl = PDFLaTeX.from_texfile(texfile)
pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=True, keep_log_file=True)
