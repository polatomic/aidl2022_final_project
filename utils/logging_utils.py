import os
import shutil
import json
import torch
import yaml
import pickle
import time

def get_file_name():
    return time.asctime()+'_checkpoint.pth.tar'

def store_data(model, optimizer, scheduler, hyperparams):
    checkpoint = {}
    checkpoint['model'] = model.state_dict()
    checkpoint['optimizer'] = optimizer.state_dict()
    checkpoint['scheduelr'] = scheduler.state_dict()
    checkpoint['hyperparams'] = hyperparams
    save_checkpoint(checkpoint, False, get_file_name())

def load_data(model, optimizer, scheduler, filename):
    checkpoint = torch.load(filename)
    model.load_state(checkpoint['model'])
    optimizer.load_state(checkpoint['optimizer'])
    scheduler.load_state(checkpoint['scheduler'])
    return checkpoint['hyperparams']

#code from: https://stackoverflow.com/questions/7100125/storing-python-dictionaries
def save_dict_to_pickle(state, basepath = os.getcwd(), filename='config.p'):
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    savepath = os.path.join(basepath, filename)
    with open(savepath, 'wb') as fp:
        pickle.dump(state, fp, protocol=pickle.HIGHEST_PROTOCOL)


def save_dict_to_json(state, basepath = os.getcwd(), filename='config.json'):
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    savepath = os.path.join(basepath, filename)
    with open(savepath, 'w') as fp:
        json.dump(state, fp)

def save_checkpoint(state, basepath = os.getcwd(), filename='checkpoint.pt'):
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    torch.save(state, os.path.join(basepath, filename))


def save_config_file(model_checkpoints_folder, args):
    if not os.path.exists(model_checkpoints_folder):
        os.makedirs(model_checkpoints_folder)
        with open(os.path.join(model_checkpoints_folder, 'config.yml'), 'w') as outfile:
            yaml.dump(args, outfile, default_flow_style=False)



