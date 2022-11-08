
import argparse

import torch
import torchvision
import torchvision.transforms as transforms
import neursafe_fl as nsfl
from train import LeNetModel, test


device = 'cuda' if torch.cuda.is_available() else 'cpu'


def get_test_dataloader(data_path, args):
    transform = transforms.Compose(
        [transforms.ToTensor(),
        transforms.Normalize(mean=[0.491, 0.482, 0.447],
                             std=[0.247, 0.243, 0.262])])

    tstset = torchvision.datasets.CIFAR10(
        root=data_path, train=False, download=True, transform=transform)
    
    if args.index_range:
        range_ = args.index_range.split(",")
        tstset = torch.utils.data.Subset(tstset,
                                         range(int(range_[0]), int(range_[1])))
    elif args.class_num:
        used_classes =[int(data) for data in args.class_num.split(",")]
        data_range = []
        for idx, (_, y) in enumerate(tstset):
            if y in used_classes:
                data_range.append(idx)
        tstset = torch.utils.data.Subset(tstset, data_range)

    test_dataloader = torch.utils.data.DataLoader(
        tstset, batch_size=64, shuffle=False, num_workers=1)

    return len(tstset), test_dataloader


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index_range", required=False,
                        help="Train data index range")
    parser.add_argument("--class_num", required=False,
                        help="Train data index range")
    args = parser.parse_args()

    data_path = nsfl.get_dataset_path("torch_cifar10_feddc")
    sample_num, test_dataload = get_test_dataloader(data_path, args)
    net = LeNetModel()
    
    nsfl.load_weights(net)
    net = net.to(device)

    accuracy, loss = test(net, test_dataload)
    metrics = {
        'sample_num': sample_num,
        'loss': loss,
        'accuracy': accuracy
    }
    print(metrics)
    nsfl.commit(metrics)
