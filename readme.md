### How to run this code? 

```bash
pip install -r requirement.txt
```

if the pygame install causes error, run:

```
sudo apt-get update
sudo apt-get install libsdl2-dev
```

If any packages are missing, please install them manually.

For the *Mindmaster platform*

```bash 
python main_interact.py
```

For reproduce experiments

Make sure you have specified the correct API and model path in experiment_codes/llms/test_local_model.py

```bash 
python experiment_codes/llms/test_local_model.py --MODEL ``your_model''
```