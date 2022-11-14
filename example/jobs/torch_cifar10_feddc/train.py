
import argparse
import torch
import torch.nn as nn
import neursafe_fl as nsfl
import torchvision.transforms as transforms
import torch.nn.functional as F
from torch.utils import data
import numpy as np

from neursafe_fl import feddc_loss
from neursafe_fl.python.sdk.utils import get_round_num


device = 'cuda' if torch.cuda.is_available() else 'cpu'


class LeNetModel(nn.Module):
    def __init__(self):
        super(LeNetModel, self).__init__()
        self.n_cls = 10
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64 , kernel_size=5)
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=64, kernel_size=5)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 5 * 5, 384) 
        self.fc2 = nn.Linear(384, 192) 
        self.fc3 = nn.Linear(192, self.n_cls)
              
        
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 64 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)

        return x


def load_data(saved_path):
    clnt_x = np.load('%s/clnt_x.npy' % saved_path, allow_pickle=True)
    clnt_y = np.load('%s/clnt_y.npy' % saved_path, allow_pickle=True)

    tst_x  = np.load('%s/tst_x.npy'  % saved_path, allow_pickle=True)
    tst_y  = np.load('%s/tst_y.npy'  % saved_path, allow_pickle=True)

    return clnt_x, clnt_y, tst_x, tst_y


class TorchDataset(torch.utils.data.Dataset):
    def __init__(self, data_x, data_y, train=False, dataset_name=''):
        self.name = dataset_name
        self.train = train
        self.transform = transforms.Compose([transforms.ToTensor()])
        self.X_data = data_x
        self.y_data = data_y.astype('float32')

    def __len__(self):
        return len(self.X_data)

    def __getitem__(self, idx):
        img = self.X_data[idx]
        if self.train:
            img = np.flip(img, axis=2).copy() if (np.random.rand() > .5) else img # Horizontal flip
            if (np.random.rand() > .5):
            # Random cropping 
                pad = 4
                extended_img = np.zeros((3,32 + pad *2, 32 + pad *2)).astype(np.float32)
                extended_img[:,pad:-pad,pad:-pad] = img
                dim_1, dim_2 = np.random.randint(pad * 2 + 1, size=2)
                img = extended_img[:,dim_1:dim_1+32,dim_2:dim_2+32]
        img = np.moveaxis(img, 0, -1)
        img = self.transform(img)

        y = self.y_data[idx]
        return img, y


def train_model_for_feddc(model, dataloader, optimizer, loss_func, scheduler,
                          sample_num, batch_size, epoch, max_norm=10):
    model.train()

    for e in range(epoch):
        epoch_loss = 0
        trn_gen_iter = dataloader.__iter__()
        for _ in range(int(np.ceil(sample_num / batch_size))):
            batch_x, batch_y = trn_gen_iter.__next__()
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            y_pred = model(batch_x)

            loss = loss_func(y_pred, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters=model.parameters(),
                                           max_norm=max_norm)
            optimizer.step()
            epoch_loss += loss.item() * list(batch_y.size())[0]
        epoch_loss /= sample_num
        print("epoch: ", e, ", loss: ", epoch_loss)
        scheduler.step()

    # Freeze model
    for params in model.parameters():
        params.requires_grad = False
    model.eval()
            
    return epoch_loss


def test(model, tst_x, tst_y):
    acc_overall = 0
    loss_overall = 0;
    loss_fn = torch.nn.CrossEntropyLoss(reduction='sum')

    batch_size = min(2000, tst_x.shape[0])
    n_tst = tst_x.shape[0]
    dataset = TorchDataset(tst_x, tst_y, dataset_name="cifar10")
    tst_gen = data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    model.eval()
    model = model.to(device)
    with torch.no_grad():
        tst_gen_iter = tst_gen.__iter__()
        for i in range(int(np.ceil(n_tst/batch_size))):
            batch_x, batch_y = tst_gen_iter.__next__()
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            y_pred = model(batch_x)

            loss = loss_fn(y_pred, batch_y.reshape(-1).long())

            loss_overall += loss.item()

            # Accuracy calculation
            y_pred = y_pred.cpu().numpy()            
            y_pred = np.argmax(y_pred, axis=1).reshape(-1)
            batch_y = batch_y.cpu().numpy().reshape(-1).astype(np.int32)
            batch_correct = np.sum(y_pred == batch_y)
            acc_overall += batch_correct

    loss_overall /= n_tst

    model.train()
    return loss_overall, acc_overall / n_tst


def main():
    """Train entry.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--client_index", required=False, type=int,
                        help="The client index")
    parser.add_argument("--data_path", required=False,
                        help="The path saved data which sampled from drichlet")
    args = parser.parse_args()

    epoch = 5
    learning_rate = 0.1
    alpha = 0.01
    weight_decay = 0.001
    lr_decay_per_round = 0.998
    batch_size = 50
    sch_step = 1
    sch_gamma = 1

    clnt_x, clnt_y, _, _ = load_data(args.data_path)
    trn_x = clnt_x[args.client_index]
    trn_y = clnt_y[args.client_index]
    dataset = TorchDataset(trn_x, trn_y, train=True, dataset_name="cifar10")
    dataloader = data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    sample_num = trn_x.shape[0]

    net = LeNetModel()
    nsfl.load_weights(net)
    net = net.to(device)

    learning_rate * (lr_decay_per_round ** (get_round_num() - 1))

    optimizer = torch.optim.SGD(net.parameters(),
                                lr=learning_rate, weight_decay=weight_decay)
    loss_func = feddc_loss(net, torch.nn.CrossEntropyLoss(reduction='sum'),
                           sample_num, batch_size, learning_rate, epoch,
                           alpha, device=device)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=sch_step,
                                                gamma=sch_gamma)

    loss = train_model_for_feddc(
        net, dataloader, optimizer, loss_func, scheduler,
        sample_num, batch_size, epoch)

    metrics = {
        'sample_num': sample_num,
        'loss': loss
    }
    print(metrics)
    nsfl.commit(metrics, net)


if __name__ == "__main__":
    main()
