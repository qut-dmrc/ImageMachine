# Image Machine documentation

The Image Machine documentation is built and configured using 
[Sphinx](https://www.sphinx-doc.org/).


To build the documentation into HTML pages (via CLI):

0. [Install Sphinx](https://www.sphinx-doc.org/en/master/usage/installation.html)
1. Navigate to the Image Machine repository root directory
2. `sphinx-build -b html docs docs/_build`
3. You can open the index page in your web browser at 
   `../ImageMachine/docs/_build/index.html`

Re-run the `sphinx-build` command as needed when changes are made to the documentation
source files.
