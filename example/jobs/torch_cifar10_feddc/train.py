
import argparse
import torch
import torch.optim as optim
import torch.nn as nn
import neursafe_fl as nsfl
import torchvision
import torchvision.transforms as transforms
import torch.nn.functional as F

from neursafe_fl import feddc_loss


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


def get_train_dataloader(data_path, args):
    transform = transforms.Compose(
        [transforms.ToTensor(),
        transforms.Normalize(mean=[0.491, 0.482, 0.447],
                             std=[0.247, 0.243, 0.262])])

    trnset = torchvision.datasets.CIFAR10(
        root=data_path, train=True , download=True, transform=transform)
    
    if args.index_range:
        range_ = args.index_range.split(",")
        trnset = torch.utils.data.Subset(trnset,
                                         range(int(range_[0]), int(range_[1])))
    elif args.class_num:
        used_classes =[int(data) for data in args.class_num.split(",")]
        data_range = []
        for idx, (_, y) in enumerate(trnset):
            if y in used_classes:
                data_range.append(idx)
        trnset = torch.utils.data.Subset(trnset, data_range)

    train_dataloader = torch.utils.data.DataLoader(
        trnset, batch_size=64, shuffle=True, num_workers=1)

    return len(trnset), train_dataloader


def train(net, dataloader, optimizer, loss_func, max_norm,
          epochs, sch_step, sch_gamma):
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer, step_size=sch_step, gamma=sch_gamma)
    net.train()
    for epoch in range(epochs):
        for x, target in dataloader:
            x, target = x.to(device), target.to(device)

            optimizer.zero_grad()
            x.requires_grad = False
            target.requires_grad = False
            target = target.long()
            out = net(x)
            loss = loss_func(out, target)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters=net.parameters(), max_norm=max_norm)
            optimizer.step()

        scheduler.step()
        print('Epoch: %d Loss: %f' % (epoch, loss))

    return loss.item()


def test(net, dataloader):
    net.eval()
    correct, total = 0, 0
    test_loss = 0
    loss_func = nn.CrossEntropyLoss(reduction='sum').to(device)
    with torch.no_grad():
        for x, target in dataloader:
            x, target = x.to(device), target.to(device)
            out = net(x)
            loss = loss_func(out, target.reshape(-1).long())

            test_loss += loss.item()
            _, predicted = out.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

    
    return correct / float(total), test_loss / len(dataloader)


def main():
    """Train entry.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--index_range", required=False,
                        help="Train data index range")
    parser.add_argument("--class_num", required=False,
                        help="Train data index range")
    args = parser.parse_args()

    data_path = nsfl.get_dataset_path("torch_cifar10_feddc")
    sample_num, dataloader = get_train_dataloader(data_path, args)

    net = LeNetModel()
    nsfl.load_weights(net)
    net = net.to(device)
    
    alpha = 0.05
    lr = 0.1
    weight_decay = 0.001
    batch_size = 64
    epoch = 2
    max_norm = 10
    sch_step = 1
    sch_gamma = 1
    optimizer = optim.SGD(net.parameters(), lr=lr, weight_decay=weight_decay)
    loss_func = feddc_loss(net, torch.nn.CrossEntropyLoss(reduction='sum'),
                           sample_num, batch_size, lr, epoch,
                           alpha, device=device)
#     loss_func = torch.nn.CrossEntropyLoss()
    loss = train(net, dataloader, optimizer, loss_func, max_norm,
                 epoch, sch_step, sch_gamma)

    metrics = {
        'sample_num': sample_num,
        'loss': loss
    }
    print(metrics)
    nsfl.commit(metrics, net)


if __name__ == "__main__":
    main()
