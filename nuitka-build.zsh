python -m nuitka \
    --company-name=AMANCA\ SOFTWARE \
    --product-name=Village\ Kids\ Pager \
    --product-version=1.0.0 \
    --copyright=Angelo\ Manca \
    --standalone \
    --enable-plugin=pyside6 \
    --macos-app-name=Village\ Kids\ Pager \
    --macos-app-mode=gui \
    --macos-signed-app-name=com.amanca.VKPager \
    --macos-sign-identity=F111476C1F677359D5FDF05340F20186C2C53930 \
    --macos-create-app-bundle \
    --macos-app-icon=data/logo.icns \
    --macos-app-protected-resource=com.apple.security.files.documents:Read\ Configs \
    bot_ui.py