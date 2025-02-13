# -*- coding: utf-8 -*-
"""Project_Interpretability.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1741QMN_OHiJc3YrY4fLXlf6B83ldcwyj
"""

import random
import sys
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torchvision
from torchvision.transforms import transforms

from PIL import Image

import cv2

#from utils.training_utils import *

device = torch.device("cuda:0")

# Load the model with trained weights
def load_resnet18_with_barlow_weights(barlow_state_dict_path, num_classes = 4):
    #Calling resnet model
    model = torchvision.models.resnet18(zero_init_residual=True)
    #model = torch.nn.DataParallel(model).to(device)
    model.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)

    model.fc = nn.Sequential( 
        nn.Linear(512, num_classes))

    #loading state dict and adapting it for the model (from Barlow Twins model to simple resnet model)
    barlow_state_dict = torch.load(barlow_state_dict_path)

    model.load_state_dict(barlow_state_dict)
    #Adapt model and add linear projector
    
    return(model)

# ResNet Class to attach a hook to the model
class ResNet(nn.Module):
    def __init__(self, Net):
        super(ResNet, self).__init__()
        
        # define the resnet152
        self.resnet = Net
        
        # isolate the feature blocks
        self.features = nn.Sequential(self.resnet.conv1,
                                      self.resnet.bn1,
                                      nn.ReLU(),
                                      nn.MaxPool2d(kernel_size=3, stride=2, padding=1, dilation=1, ceil_mode=False),
                                      self.resnet.layer1, 
                                      self.resnet.layer2, 
                                      self.resnet.layer3, 
                                      self.resnet.layer4)
        
        # average pooling layer
        self.avgpool = self.resnet.avgpool
        
        # classifier
        self.classifier = self.resnet.fc
        
        # gradient placeholder
        self.gradient = None

        #self.softmax = nn.LogSoftmax(-1)
    
    # hook for the gradients
    def activations_hook(self, grad):
        self.gradient = grad
    
    def get_gradient(self):
        return self.gradient
    
    def get_activations(self, x):
        return self.features(x)
    
    def forward(self, x):
        
        # extract the features
        x = self.features(x)
        
        # register the hook
        h = x.register_hook(self.activations_hook)
        
        # complete the forward pass
        x = self.avgpool(x)
        x = x.view((1, -1))
        x = self.classifier(x)

        return x

# Define transform
size_transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

#path to the directory with saved state dictionaries
model_save_dir = '/content/resnet18_best_state_dict.pt'

#load saved model
num_classes = 4
net = load_resnet18_with_barlow_weights(barlow_state_dict_path=model_save_dir, num_classes=num_classes).to(device)
#net

model = ResNet(net).to(device)
#model
model.eval()

# get the image
img_pth = "/content/Viral Pneumonia-1.png"
img = Image.open(img_pth) # Load image as PIL.Image
x = size_transform(img)  # Preprocess image
x = x.unsqueeze(0)  # Add batch dimension
img = x.to(device)

# get the most likely prediction of the model
pred = model(img)

label = int(pred.argmax(dim=1))
#print(pred)
#print(label)

# get the gradient of the output with respect to the parameters of the model
pred[:, label].backward()

# pull the gradients out of the model
gradients = model.get_gradient()

# pool the gradients across the channels
pooled_gradients = torch.mean(gradients, dim=[0, 2, 3])

# get the activations of the last convolutional layer
activations = model.get_activations(img).detach()

# weight the channels by corresponding gradients
for i in range(512):
    activations[:, i, :, :] *= pooled_gradients[i]
    
# average the channels of the activations
heatmap = torch.mean(activations, dim=1).squeeze().cpu()

# relu on top of the heatmap
# expression (2) in https://arxiv.org/pdf/1610.02391.pdf
heatmap = np.maximum(heatmap, 0)

# normalize the heatmap
heatmap /= torch.max(heatmap)

# draw the heatmap
plt.matshow(heatmap.squeeze())

# make the heatmap to be a numpy array
heatmap = heatmap.numpy()


img = cv2.imread(img_pth)
heatmap = cv2.resize(np.float32(heatmap), (img.shape[1], img.shape[0]))
heatmap = np.uint8(255 * heatmap)
heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
superimposed_img = heatmap * 0.4 + img
cv2.imwrite('./map.jpg', superimposed_img)

'''
Display image (for Colab only)

from google.colab.patches import cv2_imshow

img = cv2.imread("/content/map.jpg")
cv2_imshow(img)
'''