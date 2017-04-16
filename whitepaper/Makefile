all: nipopows.pdf

nipopows.pdf: *.tex *.bib algorithms/*.tex
	pdflatex nipopows.tex && \
	bibtex nipopows && \
	pdflatex nipopows.tex && \
	pdflatex nipopows.tex && \
	rm -rf *.aux *.log *.out;

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.pdf *.bbl
