"""Test parsing metadata"""

from bookbuilderpy.parse_metadata import parse_metadata


# noinspection PyPackageRequirements

def test_parse_metadata():
    text = 'blabla\n---\n# book metadata\ntitle:  An Introduction to ' \
           'Optimization Algorithms\nauthor: [Thomas Weise]\ndate: ' \
           '"\\meta{date}"\nkeywords: [Optimization, Metaheuristics, ' \
           'Local Search, Global Search]\nrights: © 2018 Thomas Weise, ' \
           'CC BY-NC-SA 4.0\nlang: en-US\n\n# reference to associated code ' \
           'repository\ncodeRepo: ' \
           'http://github.com/thomasWeise/aitoa-code.git\n\n# website ' \
           'include\nwebsite.md: README.md\n\n# bibliography metadata' \
           '\nbibliography: bibliography.bib\ncsl: ' \
           'http://www.zotero.org/styles/association-for-' \
           'computing-machinery\nlink-citations: true\n\n# HTML ' \
           'template metadata\ntemplate.html: GitHub.html5\n\n# ' \
           'LaTeX template metadata\ntemplate.latex: eisvogel-book.' \
           'latex\ntitlepage: true\ntitlepage-color: "9F2925"\ntitlepage' \
           '-text-color: "FFFFFF"\ntitlepage-rule-color: "E67015"\ntoc-' \
           'own-page: true\nlinkcolor: blue!50!black\ncitecolor: ' \
           'blue!50!black\nurlcolor: blue!50!black\ntoccolor: black\n\n' \
           '# line 1..3: hold floating objects in the same section and ' \
           'sub-section\n# line 4..6: prevent ugly broken footnotes\nheader' \
           '-includes:\n- |\n  ```{=latex}\n  \\usepackage[section,above,' \
           'below]{placeins}\n  \\let\\Oldsubsection\\subsection\n  ' \
           '\\renewcommand{\\subsection}{\\FloatBarrier\\Oldsubsection}' \
           '\n  \\addtolength{\\topskip}{0pt plus 10pt}\n  ' \
           '\\interfootnotelinepenalty=10000\n  \\raggedbottom' \
           '\n  ```\n\n# pandoc-crossref setup\ncref: true' \
           '\nchapters: true\nfigPrefix:\n  - "Figure"\n  - ' \
           '"Figures"\neqnPrefix:\n  - "Equation"\n  - ' \
           '"Equations"\ntblPrefix:\n  - "Table"\n  - ' \
           '"Tables"\nlstPrefix:\n  - "Listing"\n  - ' \
           '"Listings"\nsecPrefix:\n  - "Section"\n  - ' \
           '"Sections"\nlinkReferences: true\nlistings: ' \
           'false\ncodeBlockCaptions: true\n...\nblabla\n\n'
    d = parse_metadata(text)
    assert isinstance(d, dict)
    assert d["title"] == "An Introduction to Optimization Algorithms"
