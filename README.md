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


## Install rustfmt 2.x (pre-release)

```bash
cd ~/Projects
git clone https://github.com/rust-lang/rustfmt.git --branch rustfmt-2.0.0-rc.2
cd rustfmt
export CFG_RELEASE=nightly
export CFG_RELEASE_CHANNEL=nightly
cargo install --force --path . --locked --features rustfmt,cargo-fmt
```
