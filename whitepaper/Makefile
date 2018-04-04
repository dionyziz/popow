PACKAGE=acmart

SAMPLES = nipopows-single.tex
#	nipopows.tex
#%nipopows-single.tex

PDF = $(PACKAGE).pdf ${SAMPLES:%.tex=%.pdf}

all: ${PDF}

# nipopows.pdf: *.tex *.bib algorithms/*.tex
# 	pdflatex nipopows.tex && \
# 	bibtex nipopows && \
# 	pdflatex nipopows.tex && \
# 	pdflatex nipopows.tex && \
# 	rm -rf *.aux *.log *.out;

minimal:
	pdflatex nipopows-single.tex

%.pdf:  %.dtx   $(PACKAGE).cls
	pdflatex $<
	- bibtex $*
	pdflatex $<
	- makeindex -s gind.ist -o $*.ind $*.idx
	- makeindex -s gglo.ist -o $*.gls $*.glo
	pdflatex $<
	while ( grep -q '^LaTeX Warning: Label(s) may have changed' $*.log) \
	do pdflatex $<; done

%.cls:   %.ins %.dtx
	pdflatex $<

%.pdf:  %.tex *.tex algorithms/*.tex proofs/*.tex figures/*.png *.bib   $(PACKAGE).cls ACM-Reference-Format.bst *.sty
	pdflatex $<
	- bibtex $*
	pdflatex $<
	pdflatex $<
	while ( grep -q '^LaTeX Warning: Label(s) may have changed' $*.log) \
	do pdflatex $<; done

clean:
	$(RM)  $(PACKAGE).cls *.log *.aux \
	*.cfg *.glo *.idx *.toc \
	*.ilg *.ind *.out *.lof \
	*.lot *.bbl *.blg *.gls *.cut *.hd \
	*.dvi *.ps *.thm *.tgz *.zip *.rpi \
	*.d *.fls *.*.make

distclean: clean
	$(RM) $(PDF) *-converted-to.pdf
