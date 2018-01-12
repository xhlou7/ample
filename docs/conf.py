# -*- coding: utf-8 -*-
#
# AMPLE documentation build configuration file, created by
# sphinx-quickstart on Thu May 26 11:57:09 2016.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import sys

# Make AMPLE believe we are running it as part of CCP4
os.environ['CCP4'] = "/empty/path"

# Required by autosummary
sys.path.insert(0, os.path.abspath("."))    # for sphinxext directory
sys.path.insert(0, os.path.abspath(".."))   # for ample directory

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.6.2'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [ 
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinxext.math_symbol_table',
    'sphinxarg.ext',
    'numpydoc.numpydoc'
]

try:
    import numpydoc
except ImportError:
    msg = "Error: numpydoc must be installed before generating this documentation"
    raise ImportError(msg)

try:
    import sphinx_bootstrap_theme
except ImportError:
    msg = "Error: sphinx_bootstrap_thememust be installed before generating this documentation"
    raise ImportError(msg)

try:
    import ample.util.version
except ImportError:
    msg = "Error: AMPLE must be installed before generating its documentation"
    sys.exit(msg)

    
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'AMPLE'
copyright = u'2016-2017, University of Liverpool'
author = u'Jens Thomas, Felix Simkovic, Adam Simpkin, Ronan Keegan & Daniel Rigden'

# The short X.Y version.
version = ample.util.version.__version__
# The full version, including alpha/beta/rc tags.
release = version 

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README', '**.ipynb_checkpoints']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# If true, create autosummary automatically
#autosummary_generate = True
#autodoc_docstring_signature = True

# If set, mock the import system to have external dependencies
autodoc_mock_imports = [
    'Bio', 'conkit.io', 'conkit.plot', 'conkit._version', 'iotbx.cif', 'iotbx.file_reader', 
    'iotbx.mtz', 'iotbx.pdb', 'matplotlib', 'mmtbx.superpose', 'numpy', 'pandas', 
    'parse_arpwarp', 'parse_buccaneer', 'parse_phaser', 'parse_shelxe', 'phaser',
    'conkit.io'
]

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'bootstrap'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    # Tab name for entire site.
    'navbar_site_name': 'Home',
    # A list of tuples containing pages or urls to link to.
    'navbar_links': [
        ('Home', 'index'),
        ('Description', 'description'),
        ('Examples', 'examples'),
        ('Server', 'server'),
        ('Documentation', 'contents'),
        ('References', 'references'),
    ],
    # Render the next and previous page links in navbar. 
    'navbar_sidebarrel': False,
    # Render the current pages TOC in the navbar.)
    'navbar_pagenav': True,
    # Global TOC depth for "site" navbar tab.
    'globaltoc_depth': 2,
    # Fix navigation bar to top of page?
    'navbar_fixed_top': False,
    # Location of link to source.
    'source_link_position': "footer",
    # Bootswatch (http://bootswatch.com/) theme.
    'bootswatch_theme': "spacelab",
    # Choose Bootstrap version.
    'bootstrap_version': "3",
}

# Additional variables to be passed to templates
html_context = {
    # URL to the GitHub repository - None if unwanted
    'github_url': 'https://github.com/rigdenlab/ample.git',
}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# The name for this set of Sphinx documents.
# "<project> v<release> documentation" by default.
html_title = u'AMPLE v{0}'.format(version)

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = u'AMPLE'

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '_static/logo_ample.svg'

# The name of an image file (relative to this directory) to use as a favicon of
# the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
def setup(app):
    app.add_stylesheet("custom.css")

#html_style = 'custom.css'
html_static_path = ['_static']

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#html_extra_path = []

# If not None, a 'Last updated on:' timestamp is inserted at every page
# bottom, using the given strftime format.
# The empty string is equivalent to '%b %d, %Y'.
html_last_updated_fmt = '%d %b %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr', 'zh'
#html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# 'ja' uses this config value.
# 'zh' user can custom change `jieba` dictionary path.
#html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
#html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
htmlhelp_basename = 'AMPLEdoc'

# -- Options for LaTeX output ---------------------------------------------

#latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
#}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
#latex_documents = [
#    (master_doc, 'AMPLE.tex', u'AMPLE Documentation',
#     u'Jens Thomas, Felix Simkovic, Adam Simpkin, Ronan Keegan', 'manual'),
#]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'ample', u'AMPLE Documentation',
     [author], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'AMPLE', u'AMPLE Documentation',
     author, 'AMPLE', 'One line description of project.',
     'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False
