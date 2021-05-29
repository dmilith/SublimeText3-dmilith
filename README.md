# Install used LSP language servers:

```bash
npm install -g diagnostic-languageserver bash-languageserver elixir-language-server
```

## Useful function to install/upgrade rust-analyzer:

``` bash
update_rust_analyzer () {
    if [ ! -f "${HOME}/Downloads/rust-analyzer-mac" ]; then
        echo "Download recent version from: https://github.com/rust-analyzer/rust-analyzer/releases first!"
        return 1
    fi
    mv "${HOME}/Downloads/rust-analyzer-mac" "/usr/local/bin/rust-analyzer-mac"
    xattr -r -d com.apple.quarantine "/usr/local/bin/rust-analyzer-mac"
    chmod 755 "/usr/local/bin/rust-analyzer-mac"
    killall rust-analyzer-mac
}
```
