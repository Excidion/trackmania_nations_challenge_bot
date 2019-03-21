python3 -m venv ../ENV
source ../ENV/bin/activate
pip install --upgrade pip
pip install jupyter
python -m ipykernel install --user --name $1 --display-name "Python3 ($1)"
pip install -r requirements.txt
jupyter kernelspec list
python --version
