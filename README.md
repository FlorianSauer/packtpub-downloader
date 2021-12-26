# PacktPub Downloader

Script to download all your PacktPub books inspired by https://github.com/ozzieperez/packtpub-library-downloader

Since PacktPub restructured their website [packtpub-library-downloader](https://github.com/ozzieperez/packtpub-library-downloader) became obsolete because the downloader used webscraping. So I figured out that now PacktPub uses a REST API. Then I found which endpoint to use for downloading books and made a simple script. Feel free to fork and PR to improve. Packtpub's API isn't documented :'(

## Usage:
    pip install -r requirements.txt
	python main.py -e <email> -p <password> [-d <directory> -t <book file types> -s -v -q]

##### Example: Download books in PDF format
	python main.py -e hello@world.com -p p@ssw0rd -d ~/Desktop/packt -t pdf,epub,mobi,code

## Commandline Options
- *-e*, *--email* = Your login email
- *-p*, *--password* = Your login password
- *-d*, *--directory* = Directory to download into. Default is "media/" in the current directory
- *-t*, *--types* = Assets to download. Options are: *pdf,mobi,epub,code*
- *-s*, *--separate* = Create a separate directory for each book
- *-v*, *--verbose* = Show more detailed information
- *-q*, *--quiet* = Don't show information or progress bars
- *-f*, *--filter* = Creates hidden files for unavailable book types, so future downloads run faster. Disable this flag to recheck the availability of book types for your books.

**Book File Types**

- *pdf*: PDF format
- *mobi*: MOBI format
- *epub*: EPUB format
- *code*: Accompanying source code, saved as .zip files
