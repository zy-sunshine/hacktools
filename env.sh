TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$PYTHONPATH:$TOPDIR:$TOPDIR/py3rd

ACOM_PATH=$TOPDIR/../acom
export PYTHONPATH=$PYTHONPATH:$ACOM_PATH/djapps:$ACOM_PATH