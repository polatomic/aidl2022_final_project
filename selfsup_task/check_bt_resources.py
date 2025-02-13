#%%
from logging import exception
import ssl
import os
import time

import sys 
PROJECT_PATH =  os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.insert(0,PROJECT_PATH)

os.environ['KMP_DUPLICATE_LIB_OK']='True'
ssl._create_default_https_context = ssl._create_unverified_context

from torchvision import transforms
from self_sup_classes.barlow import *
from augmentations.transform_utils import *
import torch
from torchvision import models
from torchsummary import summary
#import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder

from tqdm import tqdm

'''
This code is used to test the resources available for the project:
    - The duration of training one epoch when changing baych size, image resolution, backbone architecture and input channels
    - Which are the best configurations that our hardware is capable of handling (before geting Out Of Memory error)

On this script we are not logging through tensorboard since it this study was perfomred at the beginning of the project 
and most functionalities were not implemented
'''

config = {
    "device":torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"), 
    "txt_logging_path": PROJECT_PATH + '/runs/time_execution/scan_model_times.txt', #path where logs are saved, change if necessary
    "selfsup_dataset_path": "F:/Datasets/chest-x-ray/COVID-19_Radiography_Dataset/", #path of the selfsup dataset, change if necessary
    "num_classes": 4,  
    "transforms_prob": 0.5,
}

#Defining the parameters
BATCH_SIZE_LIST = [2**5, 2**6, 2**7, 2**8, 2**9, 2**10, 2**11]

IMG_DIM_LIST = [
                (32,32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024),
                (32,32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024),
                (32,32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024),
                (32,32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024),
                (256, 224),(256, 240),(288, 288),(320, 300),(384, 380),
                ]
MODEL = [
        "Resnet18", "Resnet18", "Resnet18", "Resnet18", "Resnet18", "Resnet18", 
        "Resnet34", "Resnet34", "Resnet34", "Resnet34", "Resnet34", "Resnet34", 
        "Resnet50", "Resnet50", "Resnet50", "Resnet50", "Resnet50", "Resnet50",
        "Resnet101", "Resnet101", "Resnet101", "Resnet101", "Resnet101", "Resnet101",
        "EfficientnetB0", "EfficientnetB1", "EfficientnetB2", "EfficientnetB3", "EfficientnetB4"
        ]

IN_CHAN = ["CH1", "CH3"]

#Logging
with open(config["txt_logging_path"], 'a') as f:
    f.write("============Scanning running times============\n")
    f.write("Model InputChannel Batch Height Width Time\n")

#Loop over num. channels
for CH in IN_CHAN:
    #Loop over model and img res
    for M,  (IMG_DIM_H, IMG_DIM_W) in zip(MODEL, IMG_DIM_LIST):
        #Loop over batch size
        for BATCH_SIZE in BATCH_SIZE_LIST:

            torch.cuda.empty_cache( )

            if M == "Resnet18":
                print('Using Resnet18')
                model = models.resnet18(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [512, 512, 512, 512]
                if CH == "CH1":
                    model.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)####CH1
                
            elif M == "Resnet34":
                print('Using Resnet34')
                model = models.resnet34(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [512, 512, 512, 512]
                if CH == "CH1":
                    model.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)####CH1   
                
            elif M == "Resnet50":
                print('Using Resnet50')
                model = models.resnet50(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [2048, 512, 512, 512]
                if CH == "CH1":
                    model.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)####CH1    

            elif M == "Resnet101":
                print('Using Resnet101')
                model = models.resnet101(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [2048, 512, 512, 512]
                if CH == "CH1":
                    model.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)####CH1    
                
            elif M == "EfficientnetB0" :
                print('Using EfficientnetB0')
                model = models.efficientnet_b0(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [1280, 512, 512, 512] 
                if CH == "CH1":
                    model.features[0][0] = nn.Conv2d(1, 32, 3, 2, 1, bias=False)####CH1  
                
            elif M == "EfficientnetB1" :
                print('Using EfficientnetB1')
                model = models.efficientnet_b1(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [512, 512, 512, 512]
                if CH == "CH1":
                    model.features[0][0] = nn.Conv2d(1, 32, 3, 2, 1, bias=False)####CH1   
                
            elif M == "EfficientnetB2" :
                print('Using EfficientnetB2')
                model = models.efficientnet_b2(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [512, 512, 512, 512]
                if CH == "CH1":
                    model.features[0][0] = nn.Conv2d(1, 32, 3, 2, 1, bias=False)####CH1   
                
            elif M == "EfficientnetB3" :
                print('Using EfficientnetB3')
                model = models.efficientnet_b3(pretrained=False, zero_init_residual=True).to(config["device"])
                linear_layers = [512, 512, 512, 512]   
                if CH == "CH1":
                    model.features[0][0] = nn.Conv2d(1, 40, 3, 2, 1, bias=False)####CH1   
                
            elif M == "EfficientnetB4" :
                print('Using EfficientnetB4')
                model = models.efficientnet_b4(pretrained=False, zero_init_residual=True).to(config["device"])   
                linear_layers = [512, 512, 512, 512]  
                if CH == "CH1":
                    model.features[0][0] = nn.Conv2d(1, 48, 3, 2, 1, bias=False)####CH1   

            print(f"----> CHANNELS: {CH}, BATCH_SIZE: {BATCH_SIZE}, IMG_DIM: {IMG_DIM_H}, {IMG_DIM_W} ")


            if CH == "CH1":
                transform = transforms.Compose([
                                transforms.Grayscale(),####CH1
                                transforms.RandomResizedCrop((IMG_DIM_H, IMG_DIM_W),interpolation=Image.BICUBIC),
                                transforms.RandomHorizontalFlip(p=config["transforms_prob"]),
                                transforms.ToTensor(),
                            ])
            else:
                transform = transforms.Compose([
                                transforms.RandomResizedCrop((IMG_DIM_H, IMG_DIM_W),interpolation=Image.BICUBIC),
                                transforms.RandomHorizontalFlip(p=config["transforms_prob"]),
                                transforms.ToTensor(),
                            ])                

            #For the transform argument for the dataset, pass in 
            # Twins.transform_utils.Transform(transform_1, transform_2)
            #If transforms are None, the Imagenet default is used.
            dataset = ImageFolder(config["selfsup_dataset_path"], transform=Transform(transform, transform))

            loader = torch.utils.data.DataLoader(dataset,
                                                batch_size=BATCH_SIZE,
                                                shuffle=True)
            #Make the BT instance, passing the model, the latent rep layer id,
            # hidden units for the projection MLP, the tradeoff factor,
            # and the loss scale.
            learner = BarlowTwins(model, -2, linear_layers,0.5, 1).to(config["device"])

            optimizer = torch.optim.Adam(learner.parameters(), lr=0.001)

            #Single training epoch
            loss_list = []

            start_time = time.time()

            try:
                for batch_idx, ((x1,x2), _) in enumerate(tqdm(loader)):
                    
                    if batch_idx == 0:
                        print(x1.shape)

                    x1, x2 = x1.to(config["device"]), x2.to(config["device"])
                    loss = learner(x1, x2)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    loss_list.append(loss.item())

                with open(config["txt_logging_path"], 'a') as f:
                    f.write(f"{M} {CH} {BATCH_SIZE} {IMG_DIM_H} {IMG_DIM_W} {time.time() - start_time}\n")
            except Exception as e:
                print(f"\n EXCEPTION! {e} \n")
                with open(config["txt_logging_path"], 'a') as f:
                    f.write(f"{M} {CH} {BATCH_SIZE} {IMG_DIM_H} {IMG_DIM_W} OOM\n")
       

# %%

# %%
