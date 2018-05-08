# Southside Chillers

## How to Contribute

### 1) Thanks for being a pal

### 2) Set up a local environment

* Using [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), [fork this repository](https://help.github.com/articles/fork-a-repo/), and then [clone](https://help.github.com/articles/cloning-a-repository/) your fork somewhere onto your machine.
* Enter the project directory using command `cd southside.chillers.online`.
* Install the 'ghostwriter' theme. First, enter the themes directory with command `cd themes`. Then command `git clone https://github.com/jbub/ghostwriter` to install the theme.
* Return to the main project directory with command `cd ..`.
* Using [hugo](https://gohugo.io/getting-started/installing/), run the local site with a command like `hugo server -D`. You should then see a local preview available at http://localhost:1313/.

### 3) Make edits, commit your changes, and open a pull request

* ["GitHub flow"](https://guides.github.com/introduction/flow/) is a pretty good method:
    * Make a branch named something logical, like `feature/add-xalros-character-page`
    * Make edits to your heart's content. (If you need a text editor, [Visual Studio Code](https://code.visualstudio.com/docs/setup/setup-overview) and [Atom](https://flight-manual.atom.io/getting-started/sections/installing-atom/) are nice.)
    * commit your changes and push your branch to your fork
    * using the GitHub website, open a pull request from your branch to the `master` branch of this repository.

* Once the content is done and the continuous integration tests pass, We'll merge your change and the site should automatically build and deploy.