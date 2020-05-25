base_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

source "$base_dir"/env_test2.sh

export MY_EXPORTED_VAR=MyExportedVar 
NOT_EXPORTED_VAR=UnexportedVar