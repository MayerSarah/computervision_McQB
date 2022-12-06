import pandas as pd
import yaml
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt 
import torch 
import cv2
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from torch.utils.data import DataLoader

from utils.dataset_utils import SegmentationDataset
from utils.train_utils import train_fn, eval_fn
from utils.plot_utils import show_image

from models.model_backboned import SegmentationModel
from models.own_model import build_unet



CSV_FILE = "../ai_ready/silo_only.csv" 
DATA_DIR = "../ai_ready"
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
EPOCHS = 10
LR = 0.006
BATCH_SIZE = 16
IMG_SIZE = 256
ENCODER = "timm-efficientnet-b0"
WEIGHTS = "imagenet"

def train_model(test_size: float, model_name: str): 
    """ 
    This function is used to trigger the full pipeline.

    Parameters : 
    - test_size : corresponds to the size of the test set
    - model_name : corresponds to the .pt file you want to save
    """
    ## Read the path df and keep only the images where there is a silo
    df = pd.read_csv("../ai_ready/x-ai_data.csv")
    df = df.loc[df["class"] == 1]
    df.reset_index(inplace=True, drop=True)

    ## Load the train and validation dataset

    train_df, valid_df = train_test_split(df, test_size = 0.2, random_state=42)

    trainset = SegmentationDataset(train_df)
    validset = SegmentationDataset(valid_df)

    print(f'Size of trainset {len(trainset)}')
    print(f'Size of validset {len(validset)}')

    ## Feed them into the loader 

    trainloader = DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True)
    validloader = DataLoader(validset, batch_size=BATCH_SIZE)

    print(f"Total no of batches in trainloader: {len(trainloader)}")
    print(f"Total no of batches in validloader: {len(validloader)}")

    ## Load the model and send it to the CPU/GPU instance

    model =SegmentationModel()

    model.to(DEVICE)

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    ## train the model and save it in the saved_models file 

    train_loss_ls = []
    val_loss_ls = []

    best_loss = np.Inf

    for i in range(EPOCHS):
        train_loss = train_fn(trainloader, model, optimizer)
        valid_loss = eval_fn(validloader, model)

        train_loss_ls.append(train_loss)
        val_loss_ls.append(valid_loss)

        if valid_loss < best_loss :
            torch.save(model.state_dict(), "saved_models/" + model_name)
            print('SAVED_MODEL')
            best_loss = valid_loss
            print(f"Epoch : {i+1} Train Loss : {train_loss} Valid Loss : {valid_loss}")


def make_predictions(idx):
    """ 
    This function is used to make predictions on one image and display :
    - the original image
    - the ground truth mask
    - the predicted mask
    """
    df = pd.read_csv("../ai_ready/x-ai_data.csv")
    df = df.loc[df["class"] == 1]
    df.reset_index(inplace=True, drop=True)

    ## Load the train and validation dataset

    train_df, valid_df = train_test_split(df, test_size = 0.2, random_state=42)

    trainset = SegmentationDataset(train_df)
    validset = SegmentationDataset(valid_df)

    model =SegmentationModel()
    model.load_state_dict(torch.load('/content/drive/MyDrive/mckinsey_musketeers/image_segmentation/second_model.pt'))
    image, mask = validset[idx]

    logits_mask = model(image.to(DEVICE).unsqueeze(0)) #(c, h,w) --> (batch, channel, h, w)
    pred_mask = torch.sigmoid(logits_mask)
    pred_mask = (pred_mask > 0.5) * 1

    show_image(image, mask, pred_mask.detach().cpu().squeeze(0))