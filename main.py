import sys

from src.desktop.app import main as desktop_main
from src.web.app import main as web_main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        web_main()
    else:
        desktop_main()
