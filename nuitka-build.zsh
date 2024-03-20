python3.11 -m nuitka \
    --company-name=AMANCA\ SOFTWARE \
    --product-name=Village\ Kids\ Pager \
    --product-version=1.1.0 \
    --copyright=Angelo\ Manca \
    --standalone \
    --enable-plugin=pyside6 \
    --macos-app-name=Village\ Kids\ Pager \
    --macos-app-mode=gui \
    --macos-create-app-bundle \
    --macos-app-icon=data/village-kids-pager.iconset/icon_512x512.png \
    main.py

mv ./main.app ./Village\ Kids\ Pager.app
