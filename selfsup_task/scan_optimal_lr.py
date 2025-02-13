#%%
import random
import numpy as np
import torch
import torchvision
from torchvision import transforms
from torchvision.datasets import ImageFolder

import matplotlib.pylab as plt
from collections import defaultdict
from PIL import Image
import os
import ssl
import sys 

PROJECT_PATH =  os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.insert(0,PROJECT_PATH)

from self_sup_classes.barlow import BarlowTwins
from utils.training_utils import train_one_epoch, scan_best_lr
from augmentations.transform_utils import Transform

os.environ['KMP_DUPLICATE_LIB_OK']='True'
ssl._create_default_https_context = ssl._create_unverified_context


torch.cuda.empty_cache( )


config = {
    "mode": 'scan_scheduler',
    "checkpoins_basepath": os.path.join(PROJECT_PATH, f"runs/test"), #path where to save the logs, change if necessary
    "selfsup_dataset_path": "F:/Datasets/chest-x-ray/COVID-19_Radiography_Dataset/", #path of the selfsup dataset, change if necessary
    "sup_dataset_path": "F:/Datasets/chest-x-ray/COVID-19_Radiography_Dataset/", #path of the supervised dataset, change if necessary
    "random_seed": 73,
    "num_epochs": 10,
    "batch_size": 128,
    "projector_dims": [512, 512, 512, 512],
    "img_res": 224,
    "device": torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"),
    "barlow_lambda": 5e-3,
    "optimizer": "Adam",
    "lr": 2e-3,
    "transforms_prob": 0.5,
    "optimizer_weight_decay": 1e-5,
}

transform = transforms.Compose([
                transforms.Grayscale(),
                transforms.RandomResizedCrop((config["img_res"], config["img_res"]), interpolation=Image.BICUBIC),
                transforms.RandomHorizontalFlip(p=config["transforms_prob"]),
                transforms.ToTensor(),
            ])
dataset = ImageFolder(config["selfsup_dataset_path"], transform=Transform(transform, transform))

loader = torch.utils.data.DataLoader(dataset,
                                    batch_size=config["batch_size"],
                                    shuffle=True)


if config["mode"] == 'scan_lr': 
    '''
    This code is used to scan the optimal lr to train the Barlow Twins model. 
    Learnings: Inside the optimal lrs range, we will start with the highest lr value,
    we will use this lr value for our trainings.

    Observations: We have found this lr value to be, approx lr: 2e-3
    '''                              
    back_model = torchvision.models.resnet18(zero_init_residual=True)
    model = BarlowTwins(config["barlow_lambda"])
    model.add_backbone( 
                        backbone =back_model, 
                        latent_id = -2,
                        monochanel = True, 
                        backbone_name='resnet', 
                        verbose=False)

    model.add_projector(
                        projector_sizes = config["projector_dims"], 
                        verbose = True)                    

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config["optimizer_weight_decay"])
    lr_range, loss_history = scan_best_lr(loader, model, optimizer, config)
    #np.savetxt(r"D:\Documents\GitHub\aidl2022_final_project\runs\optimal_lr\scan_lr.txt", np.array(lr_range) )
    #np.savetxt(r"D:\Documents\GitHub\aidl2022_final_project\runs\optimal_lr\loss_lr.txt", np.array(loss_history) )
    plt.plot(np.array(lr_range), np.array(loss_history))
    plt.xscale("log")
    plt.savefig('scan_lr.png')
    plt.show()


elif config["mode"] == 'scan_scheduler': 
    '''
    This code is used to find the best strategy for the small-epochs training to
    iterate fast and scan possible transformations and hyperparameters. 
    Starting point, lr: 2e-3

    Examples:
    - constant lr
    - multiplicative lr
    - cosine annealing lr

    Fixing seed every iteration since the random initialization can be
    an important factor, and we want to factor it out: https://arxiv.org/abs/2109.08203

    Observations: For our combinations, cosine similarity give the best results
    '''

    back_model = torchvision.models.resnet18(zero_init_residual=True)
    model = BarlowTwins(config["barlow_lambda"])
    model.add_backbone( 
                        backbone =back_model, 
                        latent_id = -2,
                        monochanel = True, 
                        backbone_name='resnet', 
                        verbose=False)

    model.add_projector(
                        projector_sizes = config["projector_dims"], 
                        verbose = False)      

    schedulers_list = [
                    'None', 
                    'Multiplicative', 
                    'Cosine']

    sched_losses = defaultdict(list)
    for sched_name in schedulers_list:
        
        print("Training with scheduler: " + str(sched_name))

        torch.cuda.empty_cache()
        random.seed(config["random_seed"])
        np.random.seed(config["random_seed"])
        torch.manual_seed(config["random_seed"])
        #torch.use_deterministic_algorithms(True)

        #Loading dataset
        transform = transforms.Compose([
                        transforms.Grayscale(),
                        transforms.RandomResizedCrop((config["img_res"], config["img_res"]), interpolation=Image.BICUBIC),
                        transforms.RandomHorizontalFlip(p=config["transforms_prob"]),
                        transforms.ToTensor(),
                    ])
        dataset = ImageFolder(config["selfsup_dataset_path"], transform=Transform(transform, transform))

        loader = torch.utils.data.DataLoader(dataset,
                                            batch_size=config["batch_size"],
                                            shuffle=True)
        
        #Loading model
        back_model = torchvision.models.resnet18(zero_init_residual=True)
        model = BarlowTwins(config["barlow_lambda"])
        model.add_backbone( 
                            backbone =back_model, 
                            latent_id = -2,
                            monochanel = True, 
                            backbone_name='resnet', 
                            verbose=False)

        model.add_projector(
                            projector_sizes = config["projector_dims"], 
                            verbose = False)                    

        #Optimizer and scheduler
        optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config["optimizer_weight_decay"])

        
        if sched_name == 'None':
            scheduler = None
        elif sched_name == 'Multiplicative':
            scheduler = torch.optim.lr_scheduler.MultiplicativeLR(optimizer, lr_lambda=lambda epoch: 0.64, last_epoch=- 1, verbose=True)
        elif sched_name == 'Cosine':
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["num_epochs"], verbose=True)

        for epoch in range(config["num_epochs"]):
            
            losses = train_one_epoch(loader, model, optimizer, config, epoch)
            if scheduler is not None:
                scheduler.step()

            sched_losses[str(scheduler)] += losses
            print(f"---> Avg epoch loss: {np.mean(losses)}" )

        torch.save(torch.tensor(sched_losses[str(scheduler)]), sched_name +"_scan_loss.pt")
        plt.plot(range(len(sched_losses[str(scheduler)])), sched_losses[str(scheduler)])
        plt.show()
        plt.savefig(sched_name+"_sched_losses.png")


# %%
